import json
import re
import os

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
    for pattern in ITEM_BLACKLIST_PATTERNS:
        if re.search(pattern, item_id):
            return False

    # Loại bỏ tên quá ngắn (< 2 ký tự) hoặc chỉ có số
    if len(name) < 2 or name.isdigit():
        return False

    return True


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

    name = item_id.lower().split(":", 1)[1]

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
    if "netherite" in name:  base = 65536
    elif "diamond" in name:  base = 8192
    elif "emerald" in name:  base = 16384
    elif "amethyst" in name: base = 4096
    elif "gold" in name:     base = 2048
    elif "iron" in name:     base = 256
    elif "copper" in name:   base = 128
    elif "coal" in name:     base = 128
    elif "quartz" in name:   base = 256
    elif "lapis" in name:    base = 1024
    elif "redstone" in name: base = 64
    elif "obsidian" in name: base = 64
    elif "blaze" in name:    base = 1536
    elif "ender" in name or "enderman" in name: base = 1024
    elif "nether" in name:   base = 512
    elif "prismarine" in name: base = 256
    elif "slime" in name:    base = 64
    else:                    base = None  # không rõ vật liệu

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
    if "scale" in name or "claw" in name or "fang" in name or \
       "horn" in name or "feather" in name or "bone" in name:
        return base or 256

    if "fire" in name and "scale" in name:
        return 1024

    if "scale" in name:
        return base or 512

    if "meal" in name or "meat" in name:
        return base or 64

    if "shell" in name:
        return base or 256

    if "tooth" in name or "tusk" in name or "fang" in name:
        return base or 512

    if "eye" in name or "heart" in name:
        return base or 1024

    if "dragon" in name:
        return (base or 4096) * 2

    if "wither" in name:
        return (base or 2048) * 2

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
    log_file = "ListOfItemLackEMC.txt"
    json_file = "custom_emc.json"

    # ── 1. Đọc file log và trích xuất item IDs ────────────────
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                # Regex: chỉ lấy pattern modid:item_name (chữ thường, gạch dưới)
                matches = re.findall(r'\b([a-z][a-z0-9_]*:[a-z][a-z0-9_]*)\b', line)
                for match in matches:
                    if is_valid_item(match):
                        missing_items.add(match)

        print(f"✔ Tìm thấy {len(missing_items)} items hợp lệ trong file log.")
    else:
        print(f"✘ Không tìm thấy file {log_file}.")
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
    added = 0
    updated = 0
    for item in sorted(missing_items):
        emc = balance_emc(item)
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

    # ── 5. Thống kê theo mod ──────────────────────────────
    from collections import Counter
    mod_counts = Counter(e["id"].split(":")[0] for e in data["entries"])
    print("\n📊 Thống kê theo mod:")
    for mod, cnt in mod_counts.most_common():
        print(f"   {mod}: {cnt} items")


if __name__ == "__main__":
    main()