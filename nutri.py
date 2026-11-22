
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

# Create presentation
fig, ax = plt.subplots(figsize=(18, 9))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.set_xlim(0, 18)
ax.set_ylim(0, 9)
ax.axis("off")

# Project title
ax.text(
    9, 8.2,
    "NutriTrack Methodology",
    fontsize=29,
    fontweight="bold",
    color="#145A32",
    ha="center"
)

ax.text(
    9, 7.65,
    "AI-Based Food Recognition and Nutrition Tracking System",
    fontsize=14,
    color="#555555",
    ha="center"
)

# Six methodology steps
steps = [
    ("1", "USER PROFILE",
     "Age, height, weight\nand food preferences"),

    ("2", "UPLOAD MEAL",
     "Upload food photo\nor enter ingredients"),

    ("3", "AI FOOD RECOGNITION",
     "Identify food items\nand estimate portions"),

    ("4", "NUTRITION DATABASE",
     "Find calories, proteins,\ncarbs and fats"),

    ("5", "USER REVIEWS",
     "Review, edit and\nsave meal records"),

    ("6", "PERSONALIZED SUMMARY",
     "Nutrition reports\nand meal suggestions")
]

# Colors
green = "#287A45"
orange = "#F28C28"
light_green = "#EAF5E9"
light_orange = "#FFF1DF"

# Card positions
start_x = 0.35
card_width = 2.65
card_height = 3.0
gap = 0.35
card_y = 3.8

for i, (number, title, description) in enumerate(steps):

    x = start_x + i * (card_width + gap)

    color = green if i % 2 == 0 else orange
    background = light_green if i % 2 == 0 else light_orange

    # Card background
    card = FancyBboxPatch(
        (x, card_y),
        card_width,
        card_height,
        boxstyle="round,pad=0.12,rounding_size=0.2",
        facecolor=background,
        edgecolor=color,
        linewidth=2
    )
    ax.add_patch(card)

    # Number circle
    circle = Circle(
        (x + card_width / 2, card_y + 2.65),
        0.28,
        color=color
    )
    ax.add_patch(circle)

    ax.text(
        x + card_width / 2,
        card_y + 2.65,
        number,
        color="white",
        fontsize=17,
        fontweight="bold",
        ha="center",
        va="center"
    )

    # Step title
    ax.text(
        x + card_width / 2,
        card_y + 1.85,
        title,
        fontsize=12,
        fontweight="bold",
        color=color,
        ha="center",
        wrap=True
    )

    # Description
    ax.text(
        x + card_width / 2,
        card_y + 1.05,
        description,
        fontsize=11,
        color="#333333",
        ha="center",
        va="center",
        linespacing=1.7
    )

    # Arrows between cards
    if i < 5:
        ax.annotate(
            "",
            xy=(x + card_width + gap - 0.04, card_y + 1.5),
            xytext=(x + card_width + 0.03, card_y + 1.5),
            arrowprops=dict(
                arrowstyle="->",
                color=green,
                lw=2.5
            )
        )

# Explanation below flowchart
ax.text(
    0.5, 2.5,
    "PROJECT DESCRIPTION",
    fontsize=15,
    fontweight="bold",
    color=orange
)

description = (
    "NutriTrack uses Artificial Intelligence to identify food items from meal photos "
    "and estimate their portions, calories and key nutrients. Users can review and "
    "save results or enter ingredients to receive personalized meal suggestions "
    "based on their preferences. Nutrition values are estimates."
)

ax.text(
    0.5, 1.65,
    description,
    fontsize=13,
    color="#222222",
    wrap=True,
    va="center",
    linespacing=1.7
)

# Footer
ax.text(
    9, 0.55,
    "NutriTrack | Engineering Project",
    fontsize=12,
    color=green,
    ha="center",
    fontweight="bold"
)

# Save image
plt.savefig(
    "NutriTrack_Methodology.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.show()

print("NutriTrack Methodology created successfully!")
