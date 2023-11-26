import re
import shutil
import requests
import subprocess
import logging
import datetime
from bs4 import BeautifulSoup
from base_utils import setup_logger


PATH = "/home/matt/Pictures/astro/{}"
SITES = [
    {
        "site_url": "https://apod.nasa.gov/apod/astropix.html",
        "img_regexp": r"a href=\"(image\/\w*\/.*.\w*)\"",
        "img_url_path": "https://apod.nasa.gov/apod/{}",
        "label_extractor": lambda soup: soup.find_all("center")[1]
        .find("b")
        .text.strip(),
    },
    {
        "site_url": "http://astronomy.com/photos/picture-of-day",
        "img_regexp": r"src=\"/(-/media/Images/Photo of Day/.*?)\"",
        "img_url_path": "http://astronomy.com/{}",
    },
]


def dowloadPicture(site_url, img_regexp, img_url_path):
    a = requests.get(site_url, timeout=10)
    logging.info("1. Got the image name")

    regexp = re.compile(img_regexp)
    search = regexp.search(a.text)
    img_url = img_url_path.format(search.group(1))

    img = requests.get(img_url, stream=True, timeout=10)
    logging.info("2. Donwloaded image")
    if img.status_code == 200:
        img_dest = PATH.format(img_url.split("/")[-1])
        with open(img_dest, "wb") as f:
            img.raw.decode_content = True
            shutil.copyfileobj(img.raw, f)

        logging.info("3. Saved it")

        return img_dest, a.text
    raise Exception("Not Found. Recieved status code {}".format(img.status_code))


def get_label(html_page_as_text: str, extract_label_lambda=None):
    if extract_label_lambda and html_page_as_text:
        soup = BeautifulSoup(html_page_as_text, "html.parser")
        try:
            return extract_label_lambda(soup)
        except Exception as e:
            logging.exception(e)
            return None
    return None


def rework_image(img_from, site_url, label=None):
    # Resize
    img_to = PATH.format("main_tmp.png")
    subprocess.run(["convert", img_from, "-resize", "1920x1080", img_to])
    logging.info("4. Resized it")

    # Add label
    img_from = PATH.format("main_tmp.png")
    if label:
        img_to = PATH.format("main_tmp2.png")
        subprocess.run(
            [
                "convert",
                img_from,
                "-gravity",
                "center",
                "-font",
                "Ubuntu",
                "-fill",
                "white",
                "-background",
                "black",
                "-pointsize",
                "18",
                "-density",
                "150",
                "label:{}".format(label),
                "-append",
                "-resize",
                "1920x1080",
                img_to,
            ]
        )
        img_from = PATH.format("main_tmp2.png")

    # Compose with background
    # img_from = PATH.format("main_tmp.png")
    img_to = PATH.format("main.png")
    subprocess.run(
        ["composite", "-gravity", "center", img_from, PATH.format("back.png"), img_to]
    )

    logging.info("5. And merged it !")
    logging.info("Lockscreen downloaded from %s", site_url)
    return True


if __name__ == "__main__":
    setup_logger(__file__)

    try:
        last_date = ""
        with open(PATH.format("last_download.txt")) as f:
            last_date = f.readline()[:-1]
        current_date = datetime.datetime.now().isoformat().split("T")[0]
        if current_date == last_date:
            logging.info("On a déjà téléchargé l'image du jour ;)")
            exit(0)
        errors = []
        for site in SITES:
            try:
                img_to, homepage = dowloadPicture(
                    site["site_url"], site["img_regexp"], site["img_url_path"]
                )
                res = rework_image(
                    img_to,
                    site["site_url"],
                    get_label(homepage, site.get("label_extractor")),
                )
                if res:
                    with open(PATH.format("last_download.txt"), "w") as f:
                        f.write(current_date + "\n")
                    logging.info("Done :)")
                    exit(0)  # We stop the script
            except Exception as e:
                errors.append(e)
                logging.error("Not found for %s. Trying next site.", site["site_url"])
                continue
        if len(errors) > 0:
            raise errors[-1]
    except Exception as e:
        logging.exception("On garde l'image e la veille")
        exit(1)
