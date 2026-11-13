from bakery import assert_equal
from drafter import *
from dataclasses import dataclass

set_website_title("PC Build Vault")
set_site_information(
    author="Brendan McDonough",
    description="Helps you pick a computer build based on your budget.",
    sources="Thanks to the Drafter documents.",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/BrendanM2007/websiteproject"]
)
hide_debug_information()
set_website_framed(False)

