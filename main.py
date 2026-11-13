from bakery import assert_equal
from drafter import *
from dataclasses import dataclass
from PIL import Image as PILImage

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


"""
PC Build Vault (prototype)
Recommends a preset PC build for a budget. The parts list is hidden inside
an image (steganography) and is only shown if you type the right key.
You can also hide your own message in an image.
"""

USE_CASES = ["gaming", "school", "other"]
END_MARKER = "#END#"
IMAGE_SIZE = 120


@dataclass
class Build:
    name: str
    tier: str
    use_case: str
    price: int
    parts: list[str]
    key: str
    hint: str
    unlocked: bool


@dataclass
class State:
    builds: list[Build]
    budget: int
    use_case: str
    current_build: int
    secret_key: str
    hidden_message: str
    error_message: str
    only_unlocked: bool


def make_builds() -> list[Build]:
    """Makes the preset builds. Prices are rough guesses for now."""
    return [
        Build("Starter Gamer", "budget", "gaming", 650,
              ["Ryzen 5 5600", "RX 7600", "B550 board", "16GB DDR4",
               "1TB SSD", "550W PSU"], "1080", "Full HD resolution", False),
        Build("Mid Gamer", "mid", "gaming", 1100,
              ["Ryzen 7 7700", "RTX 5060 Ti", "B650 board", "32GB DDR5",
               "2TB SSD", "750W PSU"], "144", "Common gaming monitor Hz",
              False),
        Build("Top Gamer", "high", "gaming", 1900,
              ["Ryzen 7 9800X3D", "RTX 5070 Ti", "X870 board", "32GB DDR5",
               "2TB SSD", "850W PSU"], "x3d", "AMD gaming CPU suffix", False),
        Build("School Basic", "budget", "school", 450,
              ["Ryzen 5 8600G", "A620 board", "16GB DDR5", "500GB SSD",
               "450W PSU"], "apu", "CPU with built in graphics", False),
        Build("School Plus", "mid", "school", 750,
              ["Core i5-14400", "Arc B580", "B760 board", "32GB DDR5",
               "1TB SSD", "550W PSU"], "ram", "More tabs = more ___", False),
        Build("Editing Rig", "high", "other", 1300,
              ["Ryzen 9 9900X", "RTX 5060 Ti", "X870 board", "64GB DDR5",
               "2TB SSD", "750W PSU"], "render", "What you wait for after "
              "exporting a video", False),
    ]



def text_to_bits(text: str) -> list[int]:
    """Turns each character into 8 bits (0s and 1s)."""
    bits = []
    for character in text:
        number = ord(character)
        for place in [128, 64, 32, 16, 8, 4, 2, 1]:
            bits.append(number // place % 2)
    return bits


def bits_to_char(bits: list[int]) -> str:
    """Turns 8 bits back into a character."""
    number = 0
    for bit in bits:
        number = number * 2 + bit
    return chr(number)


def make_cover(seed: str) -> PILImage.Image:
    """Makes a plain gradient image. Same seed = same image."""
    shade = len(seed) * 20 % 256
    values = []
    for y in range(IMAGE_SIZE):
        for x in range(IMAGE_SIZE):
            values.append(x * 2 % 256)
            values.append(y * 2 % 256)
            values.append(shade)
    return PILImage.frombytes("RGB", (IMAGE_SIZE, IMAGE_SIZE), bytes(values))


def hide_text(image: PILImage.Image, text: str) -> PILImage.Image:
    """Hides text in a copy of the image (only works for ASCII text)."""
    values = list(image.tobytes())
    bits = text_to_bits(text + END_MARKER)
    for i in range(len(bits)):
        values[i] = values[i] - values[i] % 2 + bits[i]
    return PILImage.frombytes("RGB", image.size, bytes(values))


def read_text(image: PILImage.Image) -> str:
    """Reads hidden text out of an image until it finds END_MARKER."""
    values = list(image.tobytes())
    text = ""
    for start in range(0, len(values) - 7, 8):
        bits = []
        for value in values[start:start + 8]:
            bits.append(value % 2)
        text = text + bits_to_char(bits)
        if text.endswith(END_MARKER):
            return text[:-len(END_MARKER)]
    return ""


def lock(key: str, message: str) -> PILImage.Image:
    """Hides 'key|message' in a new cover image."""
    return hide_text(make_cover(key), key + "|" + message)


def unlock(image: PILImage.Image, key: str) -> str:
    """Returns the hidden message if the key matches, otherwise ''."""
    hidden = read_text(image)
    if key != "" and hidden.startswith(key + "|"):
        return hidden[len(key) + 1:]
    return ""


def build_image(build: Build) -> PILImage.Image:
    """The image that hides a build's parts list."""
    return lock(build.key, ", ".join(build.parts))


def best_build(builds: list[Build], budget: int, use_case: str) -> int:
    """Index of the priciest build for the use case within budget, or -1."""
    best = -1
    for i in range(len(builds)):
        build = builds[i]
        if build.use_case == use_case and build.price <= budget:
            if best == -1 or build.price > builds[best].price:
                best = i
    return best


# ---- Routes ----

@route
def index(state: State) -> Page:
    """Home page."""
    state.error_message = ""
    return Page(state, [
        "PC Build Vault",
        "Find a PC build for your budget. The parts are hidden in an image "
        "until you enter the key.",
        Button("Find My Build", budget),
        Button("Hide a Message", encode_page),
        Button("Build Gallery", gallery),
    ])


@route
def budget(state: State) -> Page:
    """Form for budget and use case."""
    return Page(state, [
        "Budget ($):",
        TextBox("budget_text", str(state.budget)),
        "Use case:",
        SelectBox("use_case", USE_CASES, state.use_case),
        state.error_message,
        Button("Find Build", find_build),
        Button("Home", index),
    ])


@route
def find_build(state: State, budget_text: str, use_case: str) -> Page:
    """Picks a build, or sends you to save_money if nothing fits."""
    state.use_case = use_case
    if not budget_text.isdigit():
        state.error_message = "Budget has to be a number"
        return budget(state)
    state.budget = int(budget_text)
    state.error_message = ""
    index_found = best_build(state.builds, state.budget, use_case)
    if index_found == -1:
        return save_money(state)
    state.current_build = index_found
    build = state.builds[index_found]
    return Page(state, [
        "Your build: " + build.name + " (" + build.tier + ")",
        "Price: $" + str(build.price),
        "Parts are locked.",
        Button("Unlock Parts", decode_page),
        Button("Home", index),
    ])


@route
def save_money(state: State) -> Page:
    """Shown when the budget is too low."""
    return Page(state, [
        "Your budget is too low for a " + state.use_case + " build.",
        "Save up some more money first.",
        Button("Try Again", budget),
        Button("Home", index),
    ])


@route
def decode_page(state: State) -> Page:
    """Shows the locked image and asks for the key."""
    build = state.builds[state.current_build]
    return Page(state, [
        "Unlock " + build.name,
        Image(build_image(build)),
        "Hint: " + build.hint,
        TextBox("secret_key", ""),
        state.error_message,
        Button("Decode", try_decode),
        Button("Home", index),
    ])


@route
def try_decode(state: State, secret_key: str) -> Page:
    """Checks the key by reading the image. Right key shows the parts."""
    build = state.builds[state.current_build]
    parts = unlock(build_image(build), secret_key)
    if parts == "":
        state.error_message = "Wrong key"
        return decode_page(state)
    build.unlocked = True
    state.error_message = ""
    return Page(state, [
        "Unlocked " + build.name + "!",
        "Parts: " + parts,
        Button("Gallery", gallery),
        Button("Home", index),
    ])


@route
def encode_page(state: State) -> Page:
    """Form to hide your own message."""
    return Page(state, [
        "Message:",
        TextArea("hidden_message", state.hidden_message),
        "Key:",
        TextBox("secret_key", state.secret_key),
        state.error_message,
        Button("Hide Message", hide_message),
        Button("Home", index),
    ])


@route
def hide_message(state: State, hidden_message: str, secret_key: str) -> Page:
    """Saves the message and key, or shows an error if one is empty."""
    state.hidden_message = hidden_message
    state.secret_key = secret_key
    if hidden_message == "" or secret_key == "":
        state.error_message = "Fill in both boxes"
        return encode_page(state)
    state.error_message = ""
    return show_encoded(state)


@route
def show_encoded(state: State) -> Page:
    """Shows the image with the user's message hidden in it."""
    return Page(state, [
        "Your message is hidden in this image. Key: " + state.secret_key,
        Image(lock(state.secret_key, state.hidden_message)),
        Button("Hide Another", encode_page),
        Button("Home", index),
    ])


@route
def gallery(state: State) -> Page:
    """Lists builds and whether they're unlocked."""
    lines = ["Build Gallery",
             CheckBox("only_unlocked", state.only_unlocked),
             "Only show unlocked",
             Button("Filter", filter_gallery)]
    for build in state.builds:
        if build.unlocked:
            lines.append(build.name + " - $" + str(build.price)
                         + " - UNLOCKED: " + ", ".join(build.parts))
        elif not state.only_unlocked:
            lines.append(build.name + " - $" + str(build.price) + " - locked")
    lines.append(Button("Home", index))
    return Page(state, lines)


@route
def filter_gallery(state: State, only_unlocked: bool) -> Page:
    """Saves the checkbox and reloads the gallery."""
    state.only_unlocked = only_unlocked
    return gallery(state)


# ---- Tests ----

def new_state() -> State:
    """Starting state used in tests and to start the site."""
    return State(make_builds(), 0, "gaming", 0, "", "", "", False)


# helpers
assert_equal(text_to_bits("A"), [0, 1, 0, 0, 0, 0, 0, 1])
assert_equal(bits_to_char([0, 1, 0, 0, 0, 0, 0, 1]), "A")
assert_equal(read_text(hide_text(make_cover("x"), "hello")), "hello")
assert_equal(read_text(make_cover("x")), "")
assert_equal(unlock(lock("pw", "RTX"), "pw"), "RTX")
assert_equal(unlock(lock("pw", "RTX"), "nope"), "")
assert_equal(unlock(lock("pw", "RTX"), ""), "")
assert_equal(best_build(make_builds(), 1200, "gaming"), 1)
assert_equal(best_build(make_builds(), 100, "gaming"), -1)
assert_equal(best_build(make_builds(), 5000, "school"), 4)

# index
assert_equal(index(new_state()), Page(new_state(), [
    "PC Build Vault",
    "Find a PC build for your budget. The parts are hidden in an image "
    "until you enter the key.",
    Button("Find My Build", "budget"),
    Button("Hide a Message", "encode_page"),
    Button("Build Gallery", "gallery"),
]))

# budget
assert_equal(budget(new_state()), Page(new_state(), [
    "Budget ($):", TextBox("budget_text", "0"),
    "Use case:", SelectBox("use_case", USE_CASES, "gaming"), "",
    Button("Find Build", "find_build"), Button("Home", "index"),
]))

# find_build
test_state = new_state()
expected = new_state()
expected.budget = 1200
expected.current_build = 1
assert_equal(find_build(test_state, "1200", "gaming"), Page(expected, [
    "Your build: Mid Gamer (mid)", "Price: $1100", "Parts are locked.",
    Button("Unlock Parts", "decode_page"), Button("Home", "index"),
]))
test_state = new_state()
assert_equal(find_build(test_state, "abc", "gaming").content[4],
             "Budget has to be a number")

# save_money
test_state = new_state()
assert_equal(find_build(test_state, "100", "school"), Page(test_state, [
    "Your budget is too low for a school build.",
    "Save up some more money first.",
    Button("Try Again", "budget"), Button("Home", "index"),
]))

# decode_page
test_state = new_state()
assert_equal(decode_page(test_state), Page(test_state, [
    "Unlock Starter Gamer", Image(build_image(test_state.builds[0])),
    "Hint: Full HD resolution", TextBox("secret_key", ""), "",
    Button("Decode", "try_decode"), Button("Home", "index"),
]))

# try_decode
test_state = new_state()
assert_equal(try_decode(test_state, "1080").content[1],
             "Parts: Ryzen 5 5600, RX 7600, B550 board, 16GB DDR4, "
             "1TB SSD, 550W PSU")
assert_equal(test_state.builds[0].unlocked, True)
test_state = new_state()
assert_equal(try_decode(test_state, "720").content[4], "Wrong key")
assert_equal(test_state.builds[0].unlocked, False)

# encode_page
assert_equal(encode_page(new_state()), Page(new_state(), [
    "Message:", TextArea("hidden_message", ""),
    "Key:", TextBox("secret_key", ""), "",
    Button("Hide Message", "hide_message"), Button("Home", "index"),
]))

# hide_message + show_encoded
test_state = new_state()
assert_equal(hide_message(test_state, "", "k").content[4],
             "Fill in both boxes")
test_state = new_state()
page = hide_message(test_state, "hi", "k")
assert_equal(page.content[0], "Your message is hidden in this image. Key: k")
assert_equal(unlock(page.content[1].url, "k"), "hi")
assert_equal(show_encoded(test_state).content[1], Image(lock("k", "hi")))

# gallery + filter_gallery
test_state = new_state()
test_state.builds[0].unlocked = True
assert_equal(gallery(test_state).content[4],
             "Starter Gamer - $650 - UNLOCKED: Ryzen 5 5600, RX 7600, "
             "B550 board, 16GB DDR4, 1TB SSD, 550W PSU")
assert_equal(gallery(test_state).content[5], "Mid Gamer - $1100 - locked")
assert_equal(len(filter_gallery(test_state, True).content), 6)
assert_equal(test_state.only_unlocked, True)



start_server(new_state())
