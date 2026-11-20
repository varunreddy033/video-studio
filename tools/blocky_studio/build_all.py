"""Build the blocky studio pack into assets/blocky3d/studio:  bin/python -I tools/blocky_studio/build_all.py [ids]."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characters as C  # noqa: E402
import props as P  # noqa: E402
import props_v4  # noqa: E402,F401  (registers video-4 props into P.PROPS)
import props_v5  # noqa: E402,F401  (videos 5-7)
import props_pets  # noqa: E402,F401  (pets, eggs, statue, guardian)
import textures as T  # noqa: E402
from glb import write_glb  # noqa: E402

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "blocky3d", "studio"))


def d(*p):
    path = os.path.join(OUT, *p)
    os.makedirs(path, exist_ok=True)
    return path


def main(only=None):
    catalog = {"units": "metres, +Y up, models face +Z, base at y=0", "characters": [], "props": [], "textures": {}}

    # ---- characters
    cdir = d("models", "characters")
    for spec in C.cast():
        if only and spec["id"] not in only:
            continue
        node = C.character(spec)
        path = os.path.join(cdir, spec["id"] + ".glb")
        size = write_glb(node, path)
        catalog["characters"].append({"id": spec["id"], "file": f"models/characters/{spec['id']}.glb",
                                      "default_face": spec.get("face", "smile"), "notes": spec.get("notes", ""),
                                      "bounds": node.bounds(), "bytes": size,
                                      "rig_nodes": ["hips", "torso", "leg_L", "leg_R", "arm_L", "arm_R", "neck",
                                                    "head", "face"]})
    if not only or "chicken" in only:
        ch = C.chicken()
        write_glb(ch, os.path.join(cdir, "chicken.glb"))
        catalog["characters"].append({"id": "chicken", "file": "models/characters/chicken.glb",
                                      "notes": "Blocky white chicken (the 'good morning' rooster)", "bounds": ch.bounds()})

    # ---- props
    for pid, (fn, cat, notes) in P.PROPS.items():
        if only and pid not in only:
            continue
        node = fn()
        rel = f"models/props/{cat}/{pid}.glb"
        d("models", "props", cat)
        size = write_glb(node, os.path.join(OUT, rel))
        catalog["props"].append({"id": pid, "category": cat, "file": rel, "notes": notes,
                                 "bounds": node.bounds(), "bytes": size})

    # ---- loose textures
    fdir = d("textures", "faces")
    for e in T.FACE_EXPRESSIONS:
        T.face(e).save(os.path.join(fdir, f"face_{e}.png"))
        T.face(e, lash=True).save(os.path.join(fdir, f"face_{e}_lashes.png"))
    catalog["textures"]["faces"] = T.FACE_EXPRESSIONS

    odir = d("textures", "outfits")
    outfits = {
        "stripes_green_black": T.stripes((25, 25, 25), (60, 200, 60), n=7),
        "stripes_red_white": T.stripes((240, 240, 240), (210, 40, 40), n=7),
        "hoodie_yellow": T.hoodie_front((250, 200, 30)), "hoodie_green": T.hoodie_front((70, 170, 110)),
        "hoodie_red": T.hoodie_front((210, 50, 50)), "suit_black": T.suit_front((40, 40, 45)),
        "suit_gold_sequin_bowtie": T.suit_front((200, 150, 40), bowtie=True, sparkle=True),
        "school_uniform_black": T.school_uniform(), "school_uniform_brown": T.school_uniform((95, 60, 40)),
        "jersey_blue_10": T.jersey((30, 50, 160)), "varsity_red_white": T.varsity_jacket(),
        "academy_tee_blue": T.academy_tee(), "pixel_smiley_tee_green": T.pixel_face_tee(),
        "text_tee_real_men_wear_pink": T.text_tee(), "knit_stripes": T.knit_stripes(), "hearts_pattern": T.hearts_pattern(),
        "crest_blazer": T.crest_blazer(), "patterned_pants_grey": T.patterned_pants(), "hoodie_yellow_green_strings": T.hoodie_front((245, 195, 30), (40, 180, 140)), "overalls": T.overalls(), "pajama_pink": T.pajama(),
        "button_shirt_orange": T.button_shirt(), "dress_pink": T.dress_pink(),
        "plaid_grey": T.plaid((45, 45, 50), (110, 110, 120)), "plaid_red": T.plaid((170, 30, 40), (40, 30, 30)),
    }
    for k, im in outfits.items():
        im.save(os.path.join(odir, f"{k}.png"))
    catalog["textures"]["outfits"] = sorted(outfits)

    sdir = d("textures", "signs")
    signs = {
        "shop_lamps_bulbs": T.sign("LAMPS & BULBS", bg=(20, 30, 70)),
        "shop_mushrooms": T.sign("MUSHROOMS", bg=(20, 30, 70)),
        "shop_cafe": T.sign("Cafe~", bg=(235, 235, 240), fg=(120, 120, 130)),
        "power_plant": T.sign("POWER PLANT", bg=(20, 30, 90), fg=(250, 220, 60)),
        "cafeteria": T.sign("CAFETERIA", bg=(250, 210, 40), fg=(30, 50, 120)),
        "costume_contest": T.sign("COSTUME CONTEST", bg=(120, 30, 140), fg=(255, 220, 245)),
        "town_rule_example": T.sign("NO UMBRELLAS AFTER DARK", bg=(250, 245, 230), fg=(170, 20, 20), border=(170, 20, 20)),
        "newspaper_front": T.newspaper("KID SEWS\nDOLL DRESSES!", "EXTRA! SPECIAL EDITION"),
        "newspaper_blank": T.newspaper("BREAKING\nNEWS", "SPECIAL EDITION"),
        "chalkboard_history_of_dust": T.chalkboard(["HISTORY OF DUST", "chapter 1: what is dust?",
                                                    "chapter 2: more dust", "dust + dust = dust"]),
        "poster_starlight_princess": T.poster(),
        "speech_good_morning": T.speech_bubble("GOOD MORNING!"),
        "speech_blank": T.speech_bubble(" "),
        "mood_dial_face": T.mood_dial(),
        "caption_example_green": T.caption_card("TOWN", True),
        "caption_example_white": T.caption_card("in this", False),
    }
    signs.update({
        "neon_no_robot_found": T.neon_text("NO ROBOT\nFOUND"), "ranking_board": T.ranking_board(),
        "hall_of_fame_titan_zero": T.hall_of_fame(), "ecg_screen": T.ecg_screen(),
        "emblem_titan_cyan": T.emblem((80, 220, 255)), "emblem_titan_red": T.emblem((255, 80, 60)),
        "emblem_titan_gold": T.emblem((255, 200, 30)), "sign_mega_arena": T.sign("MEGA ARENA", bg=(120, 90, 40),
                                                                                fg=(255, 240, 200), serif=True),
        "sign_robot_academy": T.sign("ROBOT ACADEMY", bg=(40, 60, 160), fg=(255, 230, 120), serif=True,
                                     border=(255, 210, 40)),
        "titan_zero_vanished": T.neon_text("TITAN ZERO\nVANISHED", color=(200, 200, 200), bg=(30, 30, 30)),
        "caption_example_yellow": T.caption_card("robots", False, yellow=True),
        "phone_chat_practice_number": T.phone_chat(), "phone_class_trip_photo": T.museum_photo(),
        "sticky_note_practice": T.sticky_note(), "no_phones_in_class": T.sign("NO PHONES IN CLASS", bg=(255, 255, 255),
                                                                              fg=(200, 30, 30), border=(200, 30, 30)),
        "go_tigers": T.sign("GO TIGERS", bg=(30, 30, 30), fg=(255, 140, 30)),
        "composition_cover": T.composition_cover(), "lined_paper_compliments": T.lined_paper(),
        "night_sky_poster": T.night_sky_poster(), "banner_picture_day": T.banner_picture_day(),
        "bulletin_board": T.bulletin_board(), "class_photo": T.photo_print(), "cash_bill": T.cash_bills(),
        "caption_example_orange": T.caption_card("PRACTICE", False, color=(255, 120, 30)),
    })
    for i in range(1, 31):
        signs[f"calendar_day_{i:02d}"] = T.calendar_page("NOVEMBER", f"DAY {i}")
    for wd in ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"):
        signs[f"calendar_{wd.lower()}"] = T.calendar_page("NOVEMBER", wd)
    for k, im in signs.items():
        im.save(os.path.join(sdir, f"{k}.png"))
    catalog["textures"]["signs"] = sorted(signs)

    udir = d("textures", "surfaces")
    surf = {"wood_light": T.wood((205, 160, 100)), "wood_dark": T.wood((110, 65, 40)), "wood_purple": T.wood((150, 110, 170)),
            "brick_red": T.brick(), "brick_dark": T.brick((70, 70, 75), (40, 40, 45)), "siding_white": T.siding(),
            "siding_pink": T.siding((245, 185, 205)), "siding_navy": T.siding((60, 80, 140)),
            "window_day": T.window_grid(), "window_lit": T.window_grid(lit=True), "road": T.road(),
            "tiles_floor": T.tiles(), "cobble": T.cobble(), "grass": T.grass(), "moss": T.moss(),
            "skyscraper_blue": T.skyscraper((63, 134, 230)), "skyscraper_pink": T.skyscraper((232, 122, 168), seed=2),
            "soccer_ball_dots": T.soccer_ball(), "hardwood_red": T.wood((120, 50, 30), seed=9, planks=8),
            "bookshelf_spines": T.book_spines()}
    for k, im in surf.items():
        im.save(os.path.join(udir, f"{k}.png"))
    catalog["textures"]["surfaces"] = sorted(surf)

    kdir = d("textures", "sky_fx")
    sky = {"sky_day": T.sky_gradient((70, 150, 235), (190, 225, 250), 64, 512),
           "sky_sunset": T.sky_gradient((90, 110, 200), (255, 170, 90), 64, 512),
           "sky_dusk_purple": T.sky_gradient((60, 40, 120), (230, 150, 200), 64, 512),
           "sky_storm": T.sky_gradient((25, 28, 38), (90, 95, 110), 64, 512),
           "sky_night_stars": T.star_sky(), "rain_streaks": T.rain_streaks(), "glow_warm": T.soft_glow(),
           "glow_cyan": T.soft_glow((140, 230, 255))}
    for k, im in sky.items():
        im.save(os.path.join(kdir, f"{k}.png"))
    catalog["textures"]["sky_fx"] = sorted(sky)

    with open(os.path.join(OUT, "catalog.json"), "w") as f:
        json.dump(catalog, f, indent=1)
    print(f"{len(catalog['characters'])} characters, {len(catalog['props'])} props, "
          f"{sum(len(v) for v in catalog['textures'].values())} texture entries")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
