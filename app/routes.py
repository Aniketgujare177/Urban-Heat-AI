
from flask import Blueprint, render_template, request, send_file
from datetime import datetime
from io import BytesIO

import folium
import requests

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from .services.prediction_service import predict_heat_risk
from .services.weather_service import get_location_weather
from .services.satellite_service import analyze_vegetation

main = Blueprint("main", __name__)


# --------------------------------------------------
# CITY DATA
# --------------------------------------------------

CITY_DATA = {
    "Nashik": {
        "center": [19.9975, 73.7898],
        "vegetation": 24,
        "locations": [
            {"name": "College Road", "lat": 20.0059, "lon": 73.7621, "temp": 39, "risk": "High"},
            {"name": "Gangapur Road", "lat": 20.0067, "lon": 73.7498, "temp": 35, "risk": "Medium"},
            {"name": "Panchavati", "lat": 20.0110, "lon": 73.7900, "temp": 32, "risk": "Low"},
            {"name": "Nashik Road", "lat": 19.9700, "lon": 73.8200, "temp": 40, "risk": "High"},
        ],
    },

    "Pune": {
        "center": [18.5204, 73.8567],
        "vegetation": 28,
        "locations": [
            {"name": "Shivajinagar", "lat": 18.5308, "lon": 73.8475, "temp": 38, "risk": "High"},
            {"name": "Kothrud", "lat": 18.5074, "lon": 73.8077, "temp": 34, "risk": "Medium"},
            {"name": "Aundh", "lat": 18.5590, "lon": 73.8070, "temp": 32, "risk": "Low"},
            {"name": "Hadapsar", "lat": 18.5089, "lon": 73.9260, "temp": 40, "risk": "High"},
        ],
    },

    "Mumbai": {
        "center": [19.0760, 72.8777],
        "vegetation": 20,
        "locations": [
            {"name": "Dadar", "lat": 19.0178, "lon": 72.8478, "temp": 37, "risk": "High"},
            {"name": "Andheri", "lat": 19.1136, "lon": 72.8697, "temp": 35, "risk": "Medium"},
            {"name": "Borivali", "lat": 19.2307, "lon": 72.8567, "temp": 32, "risk": "Low"},
            {"name": "Kurla", "lat": 19.0726, "lon": 72.8845, "temp": 39, "risk": "High"},
        ],
    },

    "Nagpur": {
        "center": [21.1458, 79.0882],
        "vegetation": 22,
        "locations": [
            {"name": "Sitabuldi", "lat": 21.1458, "lon": 79.0882, "temp": 42, "risk": "High"},
            {"name": "Dharampeth", "lat": 21.1390, "lon": 79.0640, "temp": 37, "risk": "Medium"},
            {"name": "Civil Lines", "lat": 21.1538, "lon": 79.0800, "temp": 34, "risk": "Low"},
            {"name": "Manish Nagar", "lat": 21.0920, "lon": 79.0610, "temp": 41, "risk": "High"},
        ],
    },
}


# --------------------------------------------------
# LIVE WEATHER API
# --------------------------------------------------

def get_live_weather(city):

    coordinates = CITY_DATA[city]["center"]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": coordinates[0],
        "longitude": coordinates[1],
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "timezone": "Asia/Kolkata",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        current = response.json()["current"]

        return {
            "temperature": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "feels_like": current["apparent_temperature"],
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
            "time": current["time"],
            "source": "Open-Meteo",
            "is_live": True,
        }

    except (requests.RequestException, KeyError, TypeError, ValueError):
        return {
            "temperature": 35,
            "humidity": 55,
            "feels_like": 37,
            "wind_speed": 5,
            "weather_code": None,
            "time": "Sample data",
            "source": "Demo data",
            "is_live": False,
        }

# --------------------------------------------------
# GET LIVE WEATHER FOR ALL NEIGHBOURHOODS
# --------------------------------------------------

def get_city_locations_with_weather(city):

    locations = []

    for area in CITY_DATA[city]["locations"]:

        location = area.copy()

        weather = get_location_weather(
            location["lat"],
            location["lon"]
        )

        print("WEATHER DEBUG:", location["name"], weather)

        location["weather"] = weather

        if weather["is_live"]:
            location["live_temp"] = weather["temperature"]
        else:
            location["live_temp"] = None

        locations.append(location)

    return locations
# --------------------------------------------------
# HEAT MAP CREATION
# --------------------------------------------------

def create_heat_map(city, locations=None):

    city_info = CITY_DATA[city]

    # Reuse existing weather data when available
    if locations is None:
        locations = get_city_locations_with_weather(city)

    heat_map = folium.Map(
        location=city_info["center"],
        zoom_start=12,
        tiles="OpenStreetMap"
    )

    colors = {
        "High": "red",
        "Medium": "orange",
        "Low": "green"
    }

    for area in locations:

        live_temp = area.get("live_temp")

        if live_temp is not None:
            temperature_text = f"{live_temp}°C (Live)"
        else:
            temperature_text = f"{area['temp']}°C (Sample)"

        folium.CircleMarker(
            location=[area["lat"], area["lon"]],
            radius=12,
            popup=(
                f"<b>{area['name']}</b><br>"
                f"Temperature: {temperature_text}<br>"
                f"Demonstration risk: {area['risk']}"
            ),
            tooltip=area["name"],
            color=colors[area["risk"]],
            fill=True,
            fill_color=colors[area["risk"]],
            fill_opacity=0.7
        ).add_to(heat_map)

    return heat_map._repr_html_()


# --------------------------------------------------
# HEAT MAP PAGE ROUTE
# --------------------------------------------------

@main.route("/heat-map")
def heat_map():

    selected_city = request.args.get("city", "Nashik")

    if selected_city not in CITY_DATA:
        selected_city = "Nashik"

    locations = get_city_locations_with_weather(selected_city)

    map_html = create_heat_map(selected_city, locations)

    return render_template(
        "heat_map.html",
        selected_city=selected_city,
        cities=list(CITY_DATA.keys()),
        locations=locations,
        map_html=map_html
    )



# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------


@main.route("/")
def home():

    selected_city = request.args.get("city", "Nashik")

    if selected_city not in CITY_DATA:
        selected_city = "Nashik"

    city_info = CITY_DATA[selected_city]
    locations = get_city_locations_with_weather(selected_city)

    # Get live weather
    weather = get_live_weather(selected_city)

    # Count demonstration risk areas
    high_count = sum(
        1 for area in locations if area["risk"] == "High"
    )

    medium_count = sum(
        1 for area in locations if area["risk"] == "Medium"
    )

    low_count = sum(
        1 for area in locations if area["risk"] == "Low"
    )

    total = len(locations)

    # Lowercase keys because index.html uses .low, .medium and .high
    risk_distribution = {
        "low": round(low_count / total * 100),
        "medium": round(medium_count / total * 100),
        "high": round(high_count / total * 100),
    }

    risk_level = (
        "High" if high_count >= 2
        else "Medium" if medium_count >= 1
        else "Low"
    )

    map_html = create_heat_map(selected_city, locations)

    return render_template(
        "index.html",

        selected_city=selected_city,
        cities=list(CITY_DATA.keys()),

        # Weather variables expected by index.html
        weather_is_live=weather["is_live"],
        weather_source=weather["source"],
        weather_time=weather["time"],

        temperature=weather["temperature"],
        feels_like=weather["feels_like"],
        humidity=weather["humidity"],
        wind_speed=weather["wind_speed"],

        # Dashboard statistics
        high_risk_count=high_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,

        risk_level=risk_level,
        risk_distribution=risk_distribution,
        vegetation=city_info["vegetation"],

        map_html=map_html,
        locations=locations,
    )



@main.route("/area-analysis")
def area_analysis():

    selected_city = request.args.get("city", "Nashik")
    selected_area_name = request.args.get("area")

    if selected_city not in CITY_DATA:
        selected_city = "Nashik"

    locations = get_city_locations_with_weather(selected_city)

    high_count = sum(1 for x in locations if x["risk"] == "High")
    medium_count = sum(1 for x in locations if x["risk"] == "Medium")
    low_count = sum(1 for x in locations if x["risk"] == "Low")

    selected_area = next(
        (area.copy() for area in locations
         if area["name"] == selected_area_name),
        None
    )

    area_map = None
    recommendations = []
    weather = None
    satellite = None
    satellite_error = None

    if selected_area:

        # 1. Reuse already fetched weather
        weather = selected_area.get("weather", {})

        # 2. Fetch satellite vegetation analysis
        try:
            satellite = analyze_vegetation(
                area_name=selected_area["name"],
                latitude=selected_area["lat"],
                longitude=selected_area["lon"]
            )

        except Exception as exc:
            print(f"Satellite analysis error: {exc}")
            satellite_error = (
                "Satellite analysis is currently unavailable."
            )

        # 3. Create neighbourhood location map
        detail_map = folium.Map(
            location=[
                selected_area["lat"],
                selected_area["lon"]
            ],
            zoom_start=15,
            tiles="OpenStreetMap"
        )

        colors = {
            "High": "red",
            "Medium": "orange",
            "Low": "green"
        }

        if weather["is_live"]:
            popup_text = (
                f"<b>{selected_area['name']}</b><br>"
                f"Temperature: {weather['temperature']}°C (Live)<br>"
                f"Humidity: {weather['humidity']}%<br>"
                f"Feels Like: {weather['feels_like']}°C"
            )
        else:
            popup_text = (
                f"<b>{selected_area['name']}</b><br>"
                "Live weather unavailable"
            )

        folium.CircleMarker(
            location=[
                selected_area["lat"],
                selected_area["lon"]
            ],
            radius=15,
            popup=popup_text,
            tooltip=selected_area["name"],
            color=colors[selected_area["risk"]],
            fill=True,
            fill_color=colors[selected_area["risk"]],
            fill_opacity=0.7
        ).add_to(detail_map)

        area_map = detail_map._repr_html_()

        # 4. Cooling recommendations
        if selected_area["risk"] == "High":
            recommendations = [
                "Increase tree plantation in this area.",
                "Encourage cool roofs on buildings.",
                "Develop additional green spaces."
            ]

        elif selected_area["risk"] == "Medium":
            recommendations = [
                "Protect existing trees and vegetation.",
                "Promote rooftop gardens.",
                "Improve shaded walking areas."
            ]

        else:
            recommendations = [
                "Maintain existing green spaces.",
                "Protect trees from unnecessary removal.",
                "Continue monitoring local heat conditions."
            ]

    print("TEMPLATE DATA:", [
    (area["name"], area.get("temp"), area.get("live_temp"))
    for area in locations
])

    return render_template(
        "area_analysis.html",
        selected_city=selected_city,
        cities=list(CITY_DATA.keys()),
        locations=locations,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        selected_area=selected_area,
        area_map=area_map,
        recommendations=recommendations,
        weather=weather,
        satellite=satellite,
        satellite_error=satellite_error
    )



# --------------------------------------------------
# AI HEAT RISK PREDICTIONS
# --------------------------------------------------

@main.route("/predictions", methods=["GET", "POST"])
def predictions():

    selected_city = request.values.get("city", "Nashik")
    selected_area_name = request.values.get("area", "")

    if selected_city not in CITY_DATA:
        selected_city = "Nashik"

    locations = CITY_DATA[selected_city]["locations"]

    selected_area = next(
        (
            area for area in locations
            if area["name"] == selected_area_name
        ),
        None
    )

    weather = None
    prediction = None
    error = None

    form_values = {
        "vegetation": CITY_DATA[selected_city]["vegetation"],
        "built_up_density": 85
    }

    # Fetch live weather when a neighbourhood is selected
    if selected_area:
        weather = get_location_weather(
            selected_area["lat"],
            selected_area["lon"]
        )

    if request.method == "POST":

        try:

            if not selected_area:
                raise ValueError("Please select a neighbourhood first.")

            if not weather or not weather["is_live"]:
                raise ValueError(
                    "Live weather is unavailable. Please try again."
                )

            form_values = {
                "vegetation": float(request.form["vegetation"]),
                "built_up_density": float(
                    request.form["built_up_density"]
                )
            }

            limits = {
                "vegetation": (5, 80),
                "built_up_density": (10, 100)
            }

            for field, (minimum, maximum) in limits.items():

                value = form_values[field]

                if not minimum <= value <= maximum:
                    raise ValueError(
                        f"{field.replace('_', ' ').title()} "
                        f"must be between {minimum} and {maximum}."
                    )

            # Use live weather with manually supplied land data
            prediction = predict_heat_risk(
                temperature=weather["temperature"],
                humidity=weather["humidity"],
                vegetation=form_values["vegetation"],
                wind_speed=weather["wind_speed"],
                built_up_density=form_values["built_up_density"]
            )

        except (ValueError, KeyError) as exc:
            error = str(exc)

        except (FileNotFoundError, OSError) as exc:
            error = f"Prediction model unavailable: {exc}"

    return render_template(
        "predictions.html",
        cities=list(CITY_DATA.keys()),
        locations=locations,
        selected_city=selected_city,
        selected_area_name=selected_area_name,
        selected_area=selected_area,
        weather=weather,
        prediction=prediction,
        form_values=form_values,
        error=error
    )


# --------------------------------------------------
# AI RECOMMENDATIONS
# --------------------------------------------------

@main.route("/recommendations")
def recommendations():

    selected_city = request.args.get("city", "Nashik")

    if selected_city not in CITY_DATA:
        selected_city = "Nashik"

    locations = CITY_DATA[selected_city]["locations"]

    recommendations_list = []

    # Recommendation database based on risk level
    recommendation_database = {

        "High": [
            {
                "title": "Increase Urban Tree Plantation",
                "description": "Prioritize tree plantation along roads, residential areas and exposed public spaces.",
                "benefit": "Provides shade and can reduce direct solar heat exposure.",
                "priority": "High",
                "icon": "bi bi-tree-fill"
            },
            {
                "title": "Implement Cool Roof Systems",
                "description": "Encourage reflective and heat-resistant roofing materials in buildings.",
                "benefit": "Can reduce roof surface heating and indoor heat gain.",
                "priority": "High",
                "icon": "bi bi-house-fill"
            },
            {
                "title": "Develop Shaded Public Spaces",
                "description": "Install shade structures near bus stops, footpaths and public gathering areas.",
                "benefit": "Improves outdoor thermal comfort for pedestrians.",
                "priority": "High",
                "icon": "bi bi-building"
            }
        ],

        "Medium": [
            {
                "title": "Promote Rooftop Gardens",
                "description": "Encourage vegetation on suitable rooftops and terraces.",
                "benefit": "Adds green cover and may reduce roof heat absorption.",
                "priority": "Medium",
                "icon": "bi bi-flower1"
            },
            {
                "title": "Protect Existing Vegetation",
                "description": "Preserve existing trees and prevent unnecessary removal of green cover.",
                "benefit": "Maintains shade and local vegetation.",
                "priority": "Medium",
                "icon": "bi bi-tree"
            },
            {
                "title": "Improve Walking Infrastructure",
                "description": "Create shaded pedestrian routes using trees and suitable shade structures.",
                "benefit": "Reduces direct sun exposure while walking.",
                "priority": "Medium",
                "icon": "bi bi-signpost-split"
            }
        ],

        "Low": [
            {
                "title": "Maintain Existing Green Spaces",
                "description": "Continue maintaining parks, gardens and roadside vegetation.",
                "benefit": "Helps preserve existing cooling benefits.",
                "priority": "Low",
                "icon": "bi bi-flower2"
            },
            {
                "title": "Monitor Local Temperature",
                "description": "Continue monitoring environmental conditions to identify future changes.",
                "benefit": "Supports early identification of increasing heat risk.",
                "priority": "Low",
                "icon": "bi bi-thermometer-half"
            }
        ]
    }

    # Generate recommendations for each sample location
    for area in locations:

        area_recommendations = recommendation_database.get(
            area["risk"], []
        )

        for item in area_recommendations:

            recommendations_list.append({
                **item,
                "area": area["name"]
            })

    # Count recommendation priorities
    high_priority_count = sum(
        1 for item in recommendations_list
        if item["priority"] == "High"
    )

    medium_priority_count = sum(
        1 for item in recommendations_list
        if item["priority"] == "Medium"
    )

    low_priority_count = sum(
        1 for item in recommendations_list
        if item["priority"] == "Low"
    )

    return render_template(
        "recommendations.html",
        selected_city=selected_city,
        cities=list(CITY_DATA.keys()),
        recommendations=recommendations_list,
        high_priority_count=high_priority_count,
        medium_priority_count=medium_priority_count,
        low_priority_count=low_priority_count
    )



# --------------------------------------------------
# CLIMATE REPORTS
# --------------------------------------------------

@main.route("/reports")
def reports():

    selected_city = request.args.get("city", "Nashik")

    if selected_city not in CITY_DATA:
        selected_city = "Nashik"

    # Get city demonstration data
    city_info = CITY_DATA[selected_city]
    locations = city_info["locations"]

    # Count risk categories
    high_count = sum(
        1 for area in locations
        if area["risk"] == "High"
    )

    medium_count = sum(
        1 for area in locations
        if area["risk"] == "Medium"
    )

    low_count = sum(
        1 for area in locations
        if area["risk"] == "Low"
    )

    total_areas = len(locations)

    # Calculate risk distribution
    if total_areas > 0:
        risk_distribution = {
            "high": round(high_count / total_areas * 100),
            "medium": round(medium_count / total_areas * 100),
            "low": round(low_count / total_areas * 100),
        }
    else:
        risk_distribution = {
            "high": 0,
            "medium": 0,
            "low": 0,
        }

    # Current report date
    report_date = datetime.now().strftime("%d %B %Y")

    return render_template(
        "reports.html",
        selected_city=selected_city,
        cities=list(CITY_DATA.keys()),
        locations=locations,
        total_areas=total_areas,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        risk_distribution=risk_distribution,
        report_date=report_date,
    )


# --------------------------------------------------
# DOWNLOAD CLIMATE REPORT AS PDF
# --------------------------------------------------

@main.route("/reports/download")
def download_report():

    selected_city = request.args.get("city", "Nashik")

    if selected_city not in CITY_DATA:
        selected_city = "Nashik"

    locations = CITY_DATA[selected_city]["locations"]

    high_count = sum(
        1 for area in locations if area["risk"] == "High"
    )

    medium_count = sum(
        1 for area in locations if area["risk"] == "Medium"
    )

    low_count = sum(
        1 for area in locations if area["risk"] == "Low"
    )

    total_areas = len(locations)

    if total_areas:
        high_percentage = round(high_count / total_areas * 100)
        medium_percentage = round(medium_count / total_areas * 100)
        low_percentage = round(low_count / total_areas * 100)
    else:
        high_percentage = 0
        medium_percentage = 0
        low_percentage = 0

    # Create PDF in memory
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#087b43"),
        fontSize=22,
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#087b43"),
        spaceBefore=14,
        spaceAfter=8
    )

    story = []

    # Report heading
    story.append(
        Paragraph("URBAN HEAT AI", title_style)
    )

    story.append(
        Paragraph(
            "Urban Heat Risk Assessment Report",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"City: {selected_city}, Maharashtra",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Report Date: {datetime.now().strftime('%d %B %Y')}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 15))

    # Risk summary
    story.append(
        Paragraph("1. Risk Summary", heading_style)
    )

    summary_data = [
        ["Metric", "Result"],
        ["Total Areas Analysed", str(total_areas)],
        ["High Risk Areas", str(high_count)],
        ["Medium Risk Areas", str(medium_count)],
        ["Low Risk Areas", str(low_count)]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[85 * mm, 75 * mm]
    )

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087b43")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f4faf6"))
    ]))

    story.append(summary_table)

    # Risk distribution
    story.append(
        Paragraph("2. Risk Distribution", heading_style)
    )

    distribution_data = [
        ["Risk Level", "Percentage"],
        ["High", f"{high_percentage}%"],
        ["Medium", f"{medium_percentage}%"],
        ["Low", f"{low_percentage}%"]
    ]

    distribution_table = Table(
        distribution_data,
        colWidths=[85 * mm, 75 * mm]
    )

    distribution_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087b43")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 9)
    ]))

    story.append(distribution_table)

    # Neighbourhood analysis
    story.append(
        Paragraph("3. Neighbourhood Analysis", heading_style)
    )

    area_data = [
        ["Neighbourhood", "Sample Temp.", "Risk Level"]
    ]

    for area in locations:
        area_data.append([
            area["name"],
            f"{area['temp']} C",
            area["risk"]
        ])

    area_table = Table(
        area_data,
        colWidths=[75 * mm, 40 * mm, 45 * mm],
        repeatRows=1
    )

    area_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087b43")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f4faf6"))
    ]))

    story.append(area_table)

    # Recommendations
    story.append(
        Paragraph("4. Suggested Actions", heading_style)
    )

    recommendations_list = [
        "Increase tree plantation in high-risk areas.",
        "Promote reflective and cool roofing systems.",
        "Develop shaded pedestrian pathways.",
        "Protect existing vegetation and green spaces.",
        "Monitor local environmental conditions."
    ]

    for item in recommendations_list:
        story.append(
            Paragraph(f"&bull; {item}", styles["Normal"])
        )
        story.append(Spacer(1, 5))

    # Data limitations
    story.append(
        Paragraph("5. Data Limitations", heading_style)
    )

    limitations = (
        "This report uses demonstration neighbourhood data and "
        "sample temperatures. These are not verified live neighbourhood "
        "measurements. The AI prediction model uses synthetic training "
        "data and requires real-world validation. City-level weather "
        "information is separate from the demonstration area dataset."
    )

    story.append(
        Paragraph(limitations, styles["Normal"])
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "Generated by Urban Heat AI | Climate Intelligence Platform",
            styles["Italic"]
        )
    )

    # Generate PDF
    document.build(story)

    buffer.seek(0)

    filename = f"Urban_Heat_Report_{selected_city}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )

