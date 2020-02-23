import itertools
import pandas as pd

### parse list of ingredients for each brand ###################################
def salus_ingr(line):
    ingredients = (
        line.split(":")[1]
        .replace("\n", "")
        .replace("*", "")
        .replace(".", "")
        .split(",")
    )
    return [i.strip() for i in ingredients]


def sonnentor_ingr(line):
    ingredients = (
        line.split(": ")[1]
        .replace(" bio", "")
        .replace("\n", "")
        .replace(".", "")
        .split(",")
    )
    return [i.strip() for i in ingredients]


def alnatura_ingr(line):
    ingredients = (
        line.split(": ")[1]
        .replace("%", "")
        .replace("\n", "")
        .replace("*", "")
        .split(",")
    )
    ingredients = [
        "".join([i for i in s if not i.isdigit()]).strip() for s in ingredients
    ]
    return ingredients


### data preparation ###########################################################
def remove_plural(ingredients):
    for idx, i in enumerate(ingredients):
        if "en" == i[-2:]:
            ingredients[idx] = i[:-1]


def unify_verbena_ending(ingredients):
    for idx, i in enumerate(ingredients):
        if "verbene" in i:
            ingredients[idx] = i.replace("verbene", "verbena")


def remove_parts_of_plant(ingredients, parts):
    for idx, i in enumerate(ingredients):
        for part in parts:
            if part in i:
                ingredients[idx] = i.replace(part, "")


def replace_green_tea_variant(ingredients):
    for idx, i in enumerate(ingredients):
        if "Jasmin" in i:
            ingredients[idx] = "Grüntee"


################################################################################


def parse_tea_file(
    brand,
    valence,
    extend_feaures_n: int,
    tea_brands_func,
    tea_brands_ending,
    parts_of_plant,
):

    # read file with teas and get name of tea and ingredients
    with open(f"{brand}_{valence}.txt", "r") as f:
        file = f.readlines()

    start = "."
    end = tea_brands_ending[brand]

    teas = {}

    for idx, line in enumerate(file):
        if line.replace("\n", ""):
            if any(char.isdigit() for char in line):
                tea_name = line[line.find(start) + len(start) : line.rfind(end)].strip()
                if brand == "salus":
                    line = file[idx + 1]

                # parse ingredients to be more meaningful
                ingredients = tea_brands_func[brand](line)
                remove_plural(ingredients)
                replace_green_tea_variant(ingredients)
                unify_verbena_ending(ingredients)
                remove_parts_of_plant(ingredients, parts_of_plant)

                # create extra features to observe relations
                if extend_feaures_n:
                    pairs = [
                        pair
                        for pair in itertools.combinations(
                            ingredients, extend_feaures_n
                        )
                    ]
                    ingredients.extend(pairs)

                teas[tea_name] = ingredients

    return teas


def parse_teas_to_df(extend_feaures_n: int):
    tea_brands_func = {
        "salus": salus_ingr,
        "sonnentor": sonnentor_ingr,
        "alnatura": alnatura_ingr,
    }

    tea_brands_ending = {
        "salus": " –",
        "sonnentor": ":",
        "alnatura": " • Zutaten: ",
    }

    parts_of_plant = [
        "blätter",
        "früchte",
        "pulver",
        "stücke",
        "blüte",
        "extrakt",
        "wurzel",
        "schalen",
        "öl",
    ]
    results = {}
    for score, valence in enumerate(["bad", "good"]):
        val_dict = {}

        for brand in tea_brands_func:
            teas = parse_tea_file(
                brand,
                valence,
                extend_feaures_n,
                tea_brands_func,
                tea_brands_ending,
                parts_of_plant,
            )
            val_dict.update(teas)

        for tea, ingr_list in val_dict.items():
            results[tea] = (ingr_list, score)

    ingredients = [i for _, (ingr_list, _) in results.items() for i in ingr_list]
    ingredients = set(ingredients)

    df = pd.DataFrame(index=results.keys(), columns=ingredients.union(["score"]))

    for tea, (ingr, score) in results.items():
        df.loc[tea, ingr] = 1
        df.loc[tea, "score"] = score
        df = df.fillna(0)

    return df
