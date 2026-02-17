# app/data.py
MOODS = [
    {
        "id": "5",
        "tag": "happy",
        "name": "Happy",
        "emoji": "😊",
        "color": "#FFE0B2",
    },
    {
        "id": "10",
        "tag": "sad",
        "name": "Sad",
        "emoji": "😢",
        "color": "#BBDEFB"
    },
    {
        "id": "15",
        "tag": "angry",
        "name": "Angry",
        "emoji": "😠",
        "color": "#FFCDD2",
    },
    {
        "id": "20",
        "tag": "inlove",
        "name": "In Love",
        "emoji": "😍",
        "color": "#F8BBD0",
    },
    {
        "id": "25",
        "tag": "anxious",
        "name": "Anxious",
        "emoji": "😰",
        "color": "#D1C4E9",
    },
    {
        "id": "30",
        "tag": "calm",
        "name": "Calm",
        "emoji": "😌",
        "color": "#C8E6C9",
    },
    {
        "id": "35",
        "tag": "tired",
        "name": "Tired",
        "emoji": "😴",
        "color": "#E1BEE7",
    },
    {
        "id": "40",
        "tag": "excited",
        "name": "Excited",
        "emoji": "🤩",
        "color": "#FFF9C4",
    },
]

SYMPTOMS = [
    {
        "id": "5",
        "tag": "headache",
        "name": "Headache",
        "icon": "head",
        "color": "#FFCDD2",
    },
    {
        "id": "10",
        "tag": "cramps",
        "name": "Cramps",
        "icon": "body",
        "color": "#F8BBD0",
    },
    {
        "id": "15",
        "tag": "bloating",
        "name": "Bloating",
        "icon": "circle",
        "color": "#E1BEE7",
    },
    {
        "id": "20",
        "tag": "nausea",
        "name": "Nausea",
        "icon": "sad",
        "color": "#C5CAE9",
    },
    {
        "id": "25",
        "tag": "fatigue",
        "name": "Fatigue",
        "icon": "sleep",
        "color": "#BBDEFB",
    },
    {
        "id": "30",
        "tag": "backpain",
        "name": "Back Pain",
        "icon": "back",
        "color": "#B2DFDB",
    },
    {
        "id": "35",
        "tag": "tenderbreasts",
        "name": "Tender Breasts",
        "icon": "heart",
        "color": "#F0F4C3",
    },
    {
        "id": "40",
        "tag": "acne",
        "name": "Acne",
        "icon": "face",
        "color": "#FFCCBC",
    },
]

ACTIVITIES = [
    {
        "id": "5",
        "tag": "exercise",
        "label": "Exercise",
        "emoji": "💪",
        "color": "#C8E6C9",
    },
    {
        "id": "10",
        "tag": "sleep",
        "label": "Sleep",
        "emoji": "😴",
        "color": "#E1BEE7",
    },
    {
        "id": "15",
        "tag": "stress",
        "label": "Stress",
        "emoji": "😫",
        "color": "#FFCDD2",
    },
    {
        "id": "20",
        "tag": "travel",
        "label": "Travel",
        "emoji": "✈️",
        "color": "#B3E5FC",
    },
    {
        "id": "25",
        "tag": "party",
        "label": "Party",
        "emoji": "🎉",
        "color": "#FFF9C4",
    },
    {
        "id": "30",
        "tag": "work",
        "label": "Work",
        "emoji": "💼",
        "color": "#CFD8DC",
    },
    {
        "id": "35",
        "tag": "meditation",
        "label": "Meditation",
        "emoji": "🧘",
        "color": "#D1C4E9",
    },
    {
        "id": "40",
        "tag": "shopping",
        "label": "Shopping",
        "emoji": "🛍️",
        "color": "#F8BBD0",
    },
]

INTIMACY_OPTIONS = [
    {
        "id": "5",
        "tag": "protected",
        "label": "Protected",
        "emoji": "🛡️",
        "color": "#C8E6C9",
    },
    {
        "id": "10",
        "tag": "unprotected",
        "label": "Unprotected",
        "emoji": "⚠️",
        "color": "#FFCDD2",
    },
    {
        "id": "15",
        "tag": "none",
        "label": "None",
        "emoji": "🚫",
        "color": "#EEEEEE",
    },
]

FLOW_OPTIONS = [
    {
        "id": "5",
        "tag": "light",
        "label": "Light",
        "emoji": "🌸",
        "color": "#FFE0F0",
    },
    {
        "id": "10",
        "tag": "medium",
        "label": "Medium",
        "emoji": "💧",
        "color": "#E1F5FE",
    },
    {
        "id": "15",
        "tag": "heavy",
        "label": "Heavy",
        "emoji": "💦",
        "color": "#C5CAE9",
    },
    {
        "id": "20",
        "tag": "spotting",
        "label": "Spotting",
        "emoji": "🩸",
        "color": "#FFCDD2",
    },
    {
        "id": "25",
        "tag": "none",
        "label": "None",
        "emoji": "🚫",
        "color": "#EEEEEE",
    },
]

RATING_SECTIONS = [
    {
        "heading": "Body & Mind",
        "items": [
            {"id": "stress", "title": "Stress", "emoji": "😫"},
            {"id": "sleep", "title": "Sleep", "emoji": "😴"},
            {"id": "exercise", "title": "Exercise", "emoji": "💪"},
            {"id": "nutrition", "title": "Nutrition", "emoji": "🥗"},
            {"id": "energy", "title": "Energy Levels", "emoji": "⚡"},
            {
                "id": "physicalHealth",
                "title": "Physical Health",
                "emoji": "🩺",
            },
        ],
    },
    {
        "heading": "Emotions",
        "items": [
            {"id": "overallMood", "title": "Overall Mood", "emoji": "😊"},
            {"id": "anxiety", "title": "Anxiety", "emoji": "😰"},
            {"id": "focus", "title": "Focus", "emoji": "🎯"},
            {"id": "motivation", "title": "Motivation", "emoji": "🔥"},
            {"id": "selfEsteem", "title": "Self-Esteem", "emoji": "🌟"},
            {
                "id": "emotionalBalance",
                "title": "Emotional Balance",
                "emoji": "⚖️",
            },
        ],
    },
    {
        "heading": "Relationships",
        "items": [
            {"id": "intimacy", "title": "Intimacy", "emoji": "🛡️"},
            {"id": "flow", "title": "Flow", "emoji": "💧"},
            {
                "id": "emotionalSupport",
                "title": "Emotional Support",
                "emoji": "🌸",
            },
            {"id": "communication", "title": "Communication", "emoji": "💬"},
            {"id": "trust", "title": "Trust", "emoji": "🤝"},
            {
                "id": "socialConnection",
                "title": "Social Connection",
                "emoji": "🌍",
            },
        ],
    },
    {
        "heading": "Productivity & Growth",
        "items": [
            {
                "id": "workPerformance",
                "title": "Work Performance",
                "emoji": "💼",
            },
            {"id": "creativity", "title": "Creativity", "emoji": "🎨"},
            {"id": "learning", "title": "Learning", "emoji": "📚"},
            {"id": "progress", "title": "Personal Progress", "emoji": "📈"},
            {"id": "discipline", "title": "Discipline", "emoji": "⏳"},
        ],
    },
    {
        "heading": "Lifestyle",
        "items": [
            {"id": "routine", "title": "Daily Routine", "emoji": "🗓️"},
            {
                "id": "workLifeBalance",
                "title": "Work-Life Balance",
                "emoji": "⚖️",
            },
            {
                "id": "financialWellbeing",
                "title": "Financial Wellbeing",
                "emoji": "💰",
            },
            {
                "id": "environment",
                "title": "Living Environment",
                "emoji": "🏡",
            },
            {"id": "fun", "title": "Fun & Recreation", "emoji": "🎉"},
        ],
    },
]
