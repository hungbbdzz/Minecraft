import json
import re
import os
from collections import Counter

# ============================================================
# WHITELIST - chỉ lấy item từ các mod thực sự có EMC value
# (bỏ qua noise như timestamps, java:, biome names, entity IDs)
# ============================================================
KNOWN_MODS = {
    # Tech / Storage
    "ae2", "appliedenergistics2", "appliede", "extendedae",
    "sophisticatedbackpacks", "sophisticatedcore",
    "industrialforegoing",
    "immersiveengineering",
    "pneumaticcraft",
    # Magic / EMC
    "projecte", "projectexpansion", "projecteintegration",
    "mysticalagriculture", "mysticalagricultureproposal",
    "naturesaura",
    "occultism",
    "ars_nouveau",
    "quark",
    # Combat / RPG mods
    "duneons", "cataclysm", "iceandfire", "brutalbosses",
    "artifacts", "zombie_variants",
    "guardvillagers",
    # World / Biome (có drop items)
    "biomeswevegone", "ohthetreesyoullgrow",
    # Draconic
    "draconicevolution", "brandonscore",
    # Misc mods có crafting items
    "blue_skies", "evilcraft",
    "easy_mob_farm",
    "farmersdelight",
    "waystones",
    "supplementaries", "suppsquared",
    # Vanilla
    "minecraft",
}

# ============================================================
# BLACKLIST - item cụ thể cần bỏ qua dù đúng mod
# ============================================================
ITEM_BLACKLIST_PATTERNS = [
    r"^minecraft:the_",          # dimensions
    r"serverlevel",
    r"debug",                    # ae2 debug items
    r"missing_content",
    r"^duneons:abyssal",         # biome names
    r"^duneons:abom_",           # entity hit sounds
    r"_hit$",                    # sound events
    r"projectile$",              # warlus shot entities
]

ITEM_ID_PATTERN = re.compile(r'\b([a-z][a-z0-9_]*:[a-z][a-z0-9_]*)\b')
ITEM_BLACKLIST_REGEXES = [re.compile(pattern) for pattern in ITEM_BLACKLIST_PATTERNS]
LOG_FILE_CANDIDATES = (
    "ListOfItemLackEMC.txt",
    "listofitemlackemc.txt",
    "ListOfItemsLackEMC.txt",
)

BASE_MATERIAL_VALUES = [
    ("netherite", 65536),
    ("diamond", 8192),
    ("emerald", 16384),
    ("amethyst", 4096),
    ("gold", 2048),
    ("iron", 256),
    ("copper", 128),
    ("coal", 128),
    ("quartz", 256),
    ("lapis", 1024),
    ("redstone", 64),
    ("obsidian", 64),
    ("blaze", 1536),
    ("prismarine", 256),
    ("slime", 64),
]


PRECIOUS_TOKENS = (
    "netherite", "diamond", "emerald", "draconium", "chaos", "dragon",
    "wither", "artifact", "relic", "legendary", "ancient", "mythic",
)

TRIVIAL_BUILDING_TOKENS = (
    "stone", "cobble", "dirt", "sand", "gravel", "netherrack", "deepslate",
    "andesite", "diorite", "granite", "tuff", "basalt", "limestone",
    "slate", "shale", "marble", "brick", "bricks", "plank", "wood", "log",
    "stairs", "slab", "wall", "fence", "fence_gate", "trapdoor", "door",
    "button", "pressure_plate", "pane", "glass", "carpet", "wool", "leaf",
    "leaves", "sapling", "terracotta", "concrete", "mud", "clay",
)

RARE_KEYWORD_VALUES = [
    ("chaotic", 131072),
    ("awakened", 65536),
    ("draconic", 32768),
    ("dragon", 16384),
    ("wither", 8192),
    ("gauntlet", 8192),
    ("boss", 8192),
    ("artifact", 4096),
    ("relic", 4096),
    ("legendary", 4096),
    ("mythic", 4096),
]


RARITY_MOD_WEIGHTS = {
    "draconicevolution": 6,
    "cataclysm": 5,
    "iceandfire": 4,
    "duneons": 3,
    "mysticalagriculture": 2,
    "ars_nouveau": 2,
    "evilcraft": 2,
    "appliedenergistics2": 1,
    "ae2": 1,
    "industrialforegoing": 1,
}

VERY_RARE_KEYWORDS = (
    "chaotic", "awakened", "draconic", "netherite", "dragon", "wither",
    "artifact", "relic", "mythic", "legendary", "ancient", "gauntlet",
)

RARE_KEYWORDS = (
    "core", "heart", "soul", "essence", "shard", "gem", "crystal",
    "orb", "sigil", "eye", "crown", "totem", "rune", "altar",
)

UNCOMMON_KEYWORDS = (
    "ingot", "plate", "gear", "dust", "rod", "nugget", "fragment",
    "powder", "machine", "generator", "cell", "storage",
)

# ============================================================
# HARDCODED EMC - giá trị cụ thể cho items quan trọng
# (sẽ OVERRIDE lên bất kỳ giá trị hỡp lý nào khác)
# ============================================================
HARDCODED_EMC = {
    # ---- Vanilla ores ----
    "minecraft:coal_ore":                128,
    "minecraft:deepslate_coal_ore":       128,
    "minecraft:iron_ore":                256,
    "minecraft:deepslate_iron_ore":       256,
    "minecraft:copper_ore":              144,
    "minecraft:deepslate_copper_ore":    144,
    "minecraft:gold_ore":               2048,
    "minecraft:deepslate_gold_ore":      2048,
    "minecraft:nether_gold_ore":         512,
    "minecraft:redstone_ore":            128,
    "minecraft:deepslate_redstone_ore":  128,
    "minecraft:lapis_ore":               864,   # 4-9 lapis (864 = lapis = 864)
    "minecraft:deepslate_lapis_ore":     864,
    "minecraft:emerald_ore":            1024,
    "minecraft:deepslate_emerald_ore":   1024,
    "minecraft:diamond_ore":            8192,
    "minecraft:deepslate_diamond_ore":   8192,
    "minecraft:nether_quartz_ore":        80,
    "minecraft:ancient_debris":        16384,
    # ---- Vanilla raw materials ----
    "minecraft:raw_iron":                256,
    "minecraft:raw_copper":              144,
    "minecraft:raw_gold":               2048,
    # ---- Mystic Agriculture ores ----
    "mysticalagriculture:inferium_ore":           64,
    "mysticalagriculture:deepslate_inferium_ore": 64,
    "mysticalagriculture:prosperity_ore":         256,
    "mysticalagriculture:deepslate_prosperity_ore": 256,
    "mysticalagriculture:soulium_ore":            512,
    # ---- Draconic Evolution ores ----
    "draconicevolution:overworld_draconium_ore":  4096,
    "draconicevolution:deepslate_draconium_ore":  4096,
    "draconicevolution:nether_draconium_ore":     8192,
    "draconicevolution:end_draconium_ore":        16384,
    # ---- Duneons blocks (có thể có trong game) ----
    "duneons:abyssalmonumentbutton":       64,
    "duneons:abyssalmonumentbuttonon":     64,
    "duneons:abyssalstonedoor":           128,
    "duneons:abyssalstonedooropenundeons": 128,
    # ---- Misc misc ----
    "minecraft:air":                       1,
    "minecraft:goat_horn":               256,
}

# ============================================================
KNOWN_MODS_SET = KNOWN_MODS  # alias

def is_valid_item(item_id: str) -> bool:
    """Trả về True nếu item_id có vẻ là item thực sự (không phải noise)."""
    # Items trong HARDCODED_EMC luôn hợp lệ
    if item_id in HARDCODED_EMC:
        return True

    mod, name = item_id.split(":", 1)

    # Phải thuộc mod trong whitelist
    if mod not in KNOWN_MODS_SET:
        return False

    # Lọc theo blacklist patterns
    for pattern in ITEM_BLACKLIST_REGEXES:
        if pattern.search(item_id):
            return False

    # Loại bỏ tên quá ngắn (< 2 ký tự) hoặc chỉ có số
    if len(name) < 2 or name.isdigit():
        return False

    return True


def material_base_value(name: str):
    for token, value in BASE_MATERIAL_VALUES:
        if token in name:
            return value
    if "ender" in name or "enderman" in name:
        return 1024
    if "nether" in name:
        return 512
    return None


def has_precious_token(name: str) -> bool:
    return any(token in name for token in PRECIOUS_TOKENS)


def trivial_block_emc(name: str):
    if has_precious_token(name):
        return None
    if any(token in name for token in TRIVIAL_BUILDING_TOKENS):
        if any(token in name for token in ("stairs", "slab", "wall", "fence", "door", "trapdoor", "pane")):
            return 8
        if any(token in name for token in ("leaf", "leaves", "sapling", "flower", "plant")):
            return 12
        return 2
    return None


def rare_keyword_floor(name: str):
    for token, emc in RARE_KEYWORD_VALUES:
        if token in name:
            return emc
    return None


def resolve_log_file() -> str:
    for candidate in LOG_FILE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return LOG_FILE_CANDIDATES[0]


def build_item_rarity_profile(item_id: str) -> dict:
    mod, name = item_id.lower().split(":", 1)
    score = RARITY_MOD_WEIGHTS.get(mod, 0)

    if any(token in name for token in VERY_RARE_KEYWORDS):
        score += 6
    if any(token in name for token in RARE_KEYWORDS):
        score += 3
    if any(token in name for token in UNCOMMON_KEYWORDS):
        score += 1

    if any(token in name for token in TRIVIAL_BUILDING_TOKENS):
        score -= 4

    if any(token in name for token in ("ore", "block", "core", "heart", "artifact", "relic")):
        score += 1

    if score <= -2:
        tier = "trivial"
        multiplier = 0.4
        minimum = 1
    elif score <= 1:
        tier = "common"
        multiplier = 0.85
        minimum = 8
    elif score <= 5:
        tier = "uncommon"
        multiplier = 1.0
        minimum = 64
    elif score <= 9:
        tier = "rare"
        multiplier = 1.35
        minimum = 512
    elif score <= 13:
        tier = "epic"
        multiplier = 1.8
        minimum = 2048
    else:
        tier = "legendary"
        multiplier = 2.4
        minimum = 8192

    return {"tier": tier, "score": score, "multiplier": multiplier, "minimum": minimum}


def adjust_emc_with_rarity(item_id: str, emc: int, profile: dict) -> int:
    if item_id in HARDCODED_EMC or not profile:
        return emc

    _, name = item_id.lower().split(":", 1)

    # Không hạ EMC của item quý đã có giá cao
    if has_precious_token(name) and emc >= 4096:
        return emc

    adjusted = int(emc * profile["multiplier"])
    adjusted = max(adjusted, profile["minimum"])

    if profile["tier"] == "trivial":
        adjusted = min(adjusted, 24)

    return max(1, adjusted)


# ============================================================
# EMC Balancing - dựa trên tên item
# ============================================================
def balance_emc(item_id: str) -> int:
    """
    Tự động ước tính giá trị EMC dựa trên tên item.
    Hardcoded values ưu tiên cao nhất.
    """
    # Ư u tiên 1: Giá trị hardcoded cụ thể
    if item_id in HARDCODED_EMC:
        return HARDCODED_EMC[item_id]

    mod, name = item_id.lower().split(":", 1)

    cheap_block_emc = trivial_block_emc(name)
    if cheap_block_emc is not None:
        return cheap_block_emc

    rare_floor = rare_keyword_floor(name)
    if rare_floor is not None and ("ore" in name or "ingot" in name or "gem" in name or "core" in name or "heart" in name):
        return rare_floor

    # ----- Mystic Agriculture: essence & seeds -----
    if "essence" in name:
        if "inferium" in name:    return 16
        if "prudentium" in name:  return 80
        if "tertium" in name:     return 400
        if "imperium" in name:    return 2000
        if "supremium" in name:   return 10000
        if "insanium" in name:    return 50000
        # Custom MA essence: dựa trên vật liệu
        if "diamond" in name:     return 8192
        if "emerald" in name:     return 16384
        if "gold" in name:        return 2048
        if "iron" in name:        return 256
        if "coal" in name:        return 128
        if "netherite" in name:   return 65536
        if "blaze" in name:       return 1536
        if "end" in name or "ender" in name: return 1024
        if "nether" in name:      return 512
        return 200  # essence không rõ

    if "seeds" in name or "seed" in name:
        # Seeds ~ essence tương ứng x9 (vì seeds = 9 essence)
        if "inferium" in name:    return 144
        if "prudentium" in name:  return 720
        if "tertium" in name:     return 3600
        if "imperium" in name:    return 18000
        if "supremium" in name:   return 90000
        if "insanium" in name:    return 450000
        # Custom seeds
        if "diamond" in name:     return 8192 * 9
        if "emerald" in name:     return 16384 * 9
        if "gold" in name:        return 2048 * 9
        if "iron" in name:        return 256 * 9
        if "netherite" in name:   return 65536 * 9
        return 1800  # seeds không rõ

    # ----- Vật liệu quý (kiểm tra trước hình thái) -----
    base = material_base_value(name)

    # ----- Hình thái item -----
    if "ore" in name:
        return (base or 512) * 2

    if "raw" in name:
        return base or 256

    if "ingot" in name or "fragment" in name:
        return base or 256

    if "nugget" in name:
        return (base or 256) // 9

    if "dust" in name or "powder" in name:
        return base or 128

    if "gem" in name or "crystal" in name:
        return base or 2048

    if "block" in name and base:
        # Block = 9 ingots (thường)
        return base * 9

    if "chunk" in name:
        return base or 512

    if "shard" in name:
        return (base or 512) // 2

    # ----- Trang bị / Vũ khí -----
    if "sword" in name:
        return (base or 512) + 256

    if "pickaxe" in name:
        return (base or 512) + 512

    if "axe" in name:
        return (base or 512) + 512

    if "shovel" in name or "hoe" in name:
        return (base or 512) + 256

    if "scythe" in name or "spear" in name or "rapier" in name or \
       "katana" in name or "hammer" in name or "cutlass" in name:
        # Vũ khí modded thường mạnh hơn
        return (base or 768) * 2

    if "bow" in name or "crossbow" in name:
        return (base or 512) + 512

    if "helmet" in name or "cap" in name:
        return (base or 512) + 512

    if "chestplate" in name or "tunic" in name or "chest" in name:
        return (base or 512) + 1024

    if "leggings" in name or "pants" in name:
        return (base or 512) + 768

    if "boots" in name or "greaves" in name:
        return (base or 512) + 512

    if "armor" in name or "armour" in name:
        return base or 1024

    # ----- Mob drops / Combat items -----
    if "dragon" in name:
        return (base or 4096) * 2

    if "wither" in name:
        return (base or 2048) * 2

    if "fire" in name and "scale" in name:
        return 1024

    if "eye" in name or "heart" in name:
        return base or 1024

    if "scale" in name:
        return base or 512

    if "tooth" in name or "tusk" in name or "fang" in name:
        return base or 512

    if "scale" in name or "claw" in name or "fang" in name or \
       "horn" in name or "feather" in name or "bone" in name:
        return base or 256

    if "meal" in name or "meat" in name:
        return base or 64

    if "shell" in name:
        return base or 256

    if "void" in name or "chaos" in name:
        return 16384

    if "bone" in name:
        return 192

    if "spawn_egg" in name:
        return 64

    if "mob" in name or "soul" in name:
        return 512

    # ----- Farmer's Delight -----
    if "straw" in name:
        return 8
    if "rice" in name:
        return 16
    if "ham" in name or "bacon" in name:
        return 64
    if "colony" in name:
        return 64

    # ----- Waystones -----
    if "waystone" in name:
        return 4096
    if "attuned_shard" in name:
        return 1024
    if "bound_scroll" in name:
        return 512
    if "crumbling_attuned" in name:
        return 256

    # ----- Quark -----
    if "rune" in name:
        return 1024
    if "clear_shard" in name:
        return 512

    # ----- Nature's Aura -----
    if "aura_bottle" in name or "rebottling" in name:
        return 512
    if "gold_leaf" in name:
        return 2048
    if "end_flower" in name:
        return 2048

    # ----- Occultism -----
    if "tallow" in name:
        return 64

    # ----- Immersive Engineering -----
    if "creosote" in name:
        return 32
    if "slag" in name:
        return 16
    if "treated_wood" in name:
        return 96

    # ----- Pneumaticraft -----
    if "plastic" in name:
        return 128

    # ----- ExtendedAE -----
    if "entro" in name:
        return 4096

    # ----- Supplementaries -----
    if "sack" in name:
        return 256


    if "log" in name or "wood" in name or "plank" in name:
        return 32

    if "stone" in name or "cobble" in name:
        return 1

    if "sand" in name or "dirt" in name or "gravel" in name:
        return 1

    if "flower" in name or "plant" in name or "leaf" in name or \
       "leaves" in name or "sapling" in name:
        return 16

    if "mushroom" in name:
        return 32

    if "crop" in name or "wheat" in name or "carrot" in name or \
       "potato" in name or "beetroot" in name:
        return 24

    # ----- Machine / Storage blocks -----
    if "machine" in name or "generator" in name or "tank" in name or \
       "furnace" in name or "compressor" in name:
        return 4096

    if "cable" in name or "pipe" in name or "wire" in name:
        return 128

    if "cell" in name or "storage" in name:
        return 2048

    # ----- Altar / Totem / Ritual blocks -----
    if "altar" in name or "totem" in name or "ritual" in name:
        return 4096

    # ----- Tinh thể / Gem modded -----
    if any(x in name for x in ["citrine", "aquamarine", "topaz", "sapphire",
                                "peridot", "malachite", "opal", "alexandrite"]):
        if "ore" in name:   return 4096
        if "block" in name: return 4096 * 9
        return 4096

    # ----- Mod khó / boss-heavy: tăng sàn EMC nhẹ -----
    if mod in {"iceandfire", "cataclysm", "duneons", "draconicevolution"}:
        if any(x in name for x in ("essence", "shard", "core", "heart", "claw", "fang", "scale", "eye")):
            return max(base or 1024, 1024)

    # ----- Mặc định theo độ phức tạp tên -----
    # Tên càng dài/phức tạp = item modded thường có giá trị nhất định
    word_count = len(name.split('_'))
    if word_count >= 4:
        return 512  # item modded phức tạp
    elif word_count >= 2:
        return 200
    return 100


# ============================================================
# Main
# ============================================================
def main():
    # Chuyển working dir về thư mục chứa script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    missing_items = set()
    log_file = resolve_log_file()
    json_file = "custom_emc.json"
    rarity_profiles = {}

    # ── 1. Đọc file log và trích xuất item IDs ────────────────
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                # Regex: chỉ lấy pattern modid:item_name (chữ thường, gạch dưới)
                matches = ITEM_ID_PATTERN.findall(line)
                for match in matches:
                    if is_valid_item(match):
                        missing_items.add(match)

        print(f"✔ Đọc log từ: {log_file}")
        print(f"✔ Tìm thấy {len(missing_items)} items hợp lệ trong file log.")
    else:
        print(f"✘ Không tìm thấy file log thiếu EMC. Đã tìm: {LOG_FILE_CANDIDATES}")
        return

    # ── 2. Đọc custom_emc.json hiện tại ────────────────
    data = {"entries": []}
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠ File {json_file} bị lỗi JSON, tạo mới.")
    existing_entries = {entry["id"]: entry["emc"] for entry in data.get("entries", [])}

    # ── 3. Thêm EMC cho item mới + override HARDCODED ────────
    # Đảm bảo tất cả HARDCODED items đều có trong danh sách
    missing_items.update(HARDCODED_EMC.keys())
    for item in missing_items:
        rarity_profiles[item] = build_item_rarity_profile(item)

    added = 0
    updated = 0
    tier_counter = Counter(profile["tier"] for profile in rarity_profiles.values())

    for item in sorted(missing_items):
        emc = balance_emc(item)
        emc = adjust_emc_with_rarity(item, emc, rarity_profiles.get(item))
        if item not in existing_entries:
            existing_entries[item] = emc
            added += 1
        elif item in HARDCODED_EMC and existing_entries[item] != emc:
            # Luôn override với giá trị hardcoded chính xác
            existing_entries[item] = emc
            updated += 1

    # ── 4. Lưu kết quả ──────────────────────────────────────
    data["entries"] = [{"id": k, "emc": v} for k, v in sorted(existing_entries.items())]

    output_file = "custom_emc_updated.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Sync sang game config nếu tìm thấy
    game_config = r"C:\Users\hunga\AppData\Roaming\.minecraft\versions\Neo 1.21.1\config\ProjectE\custom_emc.json"
    if os.path.exists(os.path.dirname(game_config)):
        with open(game_config, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✔ Đã sync sang game: ...ProjectE\\custom_emc.json")
    else:
        print(f"⚠ Không tìm thấy thư mục game, chỉ lưu vào '{output_file}'.")

    print(f"✔ Hoàn thành! Thêm {added} mới, cập nhật {updated} items (HARDCODED).")
    print(f"✔ Tổng cộng {len(data['entries'])} items.")
    print(f"⚡ Vào game gõ: /projecte reloadEmc")

    print("\n🎯 Phân loại độ hiếm từ danh sách thiếu EMC:")
    for tier, cnt in tier_counter.most_common():
        print(f"   {tier}: {cnt} items")

    # ── 5. Thống kê theo mod ──────────────────────────────
    mod_counts = Counter(e["id"].split(":")[0] for e in data["entries"])
    print("\n📊 Thống kê theo mod:")
    for mod, cnt in mod_counts.most_common():
        print(f"   {mod}: {cnt} items")


if __name__ == "__main__":
    main()
