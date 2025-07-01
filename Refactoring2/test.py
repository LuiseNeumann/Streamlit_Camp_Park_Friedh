import folium

# === Karte erzeugen ===
m = folium.Map(location=[51.1657, 10.4515], zoom_start=6)

# === FeatureGroups ===
parks_markers = folium.FeatureGroup(name="Park Marker", overlay=True, control=False)
cemetery_markers = folium.FeatureGroup(name="Friedhof Marker", overlay=True, control=False)

# === Marker hinzufügen ===
folium.Marker([52.52, 13.405], popup="Park Berlin").add_to(parks_markers)
folium.Marker([48.1351, 11.5820], popup="Park München").add_to(parks_markers)

folium.Marker([50.1109, 8.6821], popup="Friedhof Frankfurt").add_to(cemetery_markers)
folium.Marker([53.5511, 9.9937], popup="Friedhof Hamburg").add_to(cemetery_markers)

# === Gruppen zur Karte hinzufügen ===
parks_markers.add_to(m)
cemetery_markers.add_to(m)

# === JS & CSS für GroupedLayerControl einbinden ===
plugin = """
<link rel="stylesheet" href="https://makinacorpus.github.io/Leaflet.GroupedLayerControl/dist/leaflet.groupedlayercontrol.min.css" />
<script src="https://makinacorpus.github.io/Leaflet.GroupedLayerControl/dist/leaflet.groupedlayercontrol.min.js"></script>
"""
m.get_root().html.add_child(folium.Element(plugin))

# === JS für Gruppensteuerung ===
grouped_script = f"""
<script>
  var groupedOverlays = {{
    "Parks": {{
      "Park Marker": {parks_markers.get_name()}
    }},
    "Friedhöfe": {{
      "Friedhof Marker": {cemetery_markers.get_name()}
    }}
  }};

  L.control.groupedLayers(null, groupedOverlays, {{ collapsed: false }}).addTo({m.get_name()});
</script>
"""
m.get_root().html.add_child(folium.Element(grouped_script))

# === HTML speichern ===
m.save("grouped_layer_test.html")




           try:
                # Bins definieren
                max_area = daten["area_ha"].max()
                bins = list(range(0, int(max_area) + 10, 10))
                labels = [f"{b}-{b+10}" for b in bins[:-1]]

                def histo_daten(df, methode_label):
                    tmp = df.copy()
                    tmp["Arbeiter"] = tmp["area_ha"].apply(
                        lambda x: berechne_arbeiter(x, min_pro_m2, std_pro_tag, tage_pro_jahr)
                    )
                    tmp["Marktpotenzial"] = tmp["Arbeiter"].apply(
                        lambda a: berechne_fahrradanzahl(a, arbeiter_pro_rad, methode_label)
                    )
                    tmp["Flächenklasse"] = pd.cut(tmp["area_ha"], bins=bins, labels=labels, right=False)
                    grouped = tmp.groupby("Flächenklasse", observed=True)["Marktpotenzial"].sum().reset_index()
                    grouped["Methode"] = methode_label
                    return grouped

                # Daten für alle Methoden
                daten_auf = histo_daten(gefiltert, "Aufrunden")
                daten_ab = histo_daten(gefiltert, "Abrunden") 
                daten_gl = histo_daten(gefiltert, "Gleitkomma")

                hist_all = pd.concat([daten_auf, daten_ab, daten_gl], ignore_index=True)

                if not hist_all.empty:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    sns.barplot(data=hist_all, x="Flächenklasse", y="Marktpotenzial", hue="Methode", ax=ax)
                    
                    # Achsenbeschriftung optimieren
                    plt.xticks(rotation=45)
                    ax.set_xlabel("Flächenklasse (ha)")
                    ax.set_ylabel("Anzahl Fahrräder")
                    ax.set_title("Fahrradverteilung pro Flächenklasse nach Rundungsmethode")
                    plt.tight_layout()
                    st.pyplot(fig)
                    
            except Exception as e:
                st.error(f"Fehler beim Erstellen des Histogramms: {e}")

        # Download
        st.subheader("Bericht herunterladen")
        csv_download = gefiltert.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Bericht herunterladen (CSV)", 
            data=csv_download, 
            file_name="marktpotenzial_bericht.csv",
            mime="text/csv"
        )
    else:
        st.warning("Keine Daten im ausgewählten Bereich gefunden.")