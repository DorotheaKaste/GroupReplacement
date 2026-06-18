# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 13:25:30 2025

@author: KasDL
"""

import streamlit as st
import streamlit_ext as ste
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import tempfile

#import calculation code
from calculation_group_replacements import calculate_group_replacements as calc_group


# define input variabels
label_soort_object = "soort object"
label_aantal_objecten = "aantal objecten"
label_gemiddelde_leefdtijd = "gemiddelde levensduur"
label_stdev_leefdtijd = "standaardafwijking levensduur"
label_faalpercentage = "toegestaan faalpercentage objecten"
label_tijdshorizon = "tijdshorizon berekening"
label_vervangingskosten_object = "vervangingskosten object (kEuro)"
label_rentevoet = "rentevoet"
label_N_sim = "aantal simulaties"
N_sim = 2000

# define text here
page_header = "Probabilistische berekening voor groepsvervangingen van objecten"
introduction = "Dit model simuleert de uitval van objecten in de tijd op basis van hun levensduurkansverdeling. Als een bepaalde maximale uitval is bereikt, wordt de groep objecten vervangen door nieuwe. Het model rekent uit wat de tijdstippen zijn voor groepsvervangingen van objecten over de ontwerplevensduur (tijdshorizon) en wat dit kost, uitgedrukt in netto contante waarde en equivalente jaarlijkse kosten. Dit ondersteunt de lange termijn assetplanning, de afweging over de omvang van groepsvervangingen, en geeft inzicht in het verschil in kosten tussen individuele vervangingen en groepsvervangingen." 
introduction_calculation = (f"Met de ingevoerde waarden wordt een probabilistische berekening met {N_sim} simulaties uitgevoerd om de gemiddelde tijdstippen van vervanging, zoals de hiermee verbondene kosten te berekenen.")
introduction_input = "De invoerwaarden kunnen worden aangepast aan de eigen situatie."

disclaimer = ("""Dit berekeningsmodel is ontwikkeld door Martine van den Boomen en Dorothea Kaste (Hogeschool Rotterdam) en Henk Voogt (Port of Rotterdam). 
Bij vragen stuur een email naar: d.l.kaste@hr.nl
         
Dit model is onderdeel van het project "LiveQuay: Live Insights for Bridges and Quay Walls" met projectnummer NWA.1431.20.002 van het onderzoeksprogramma NWA Urbiquay dat (gedeeltelijk) gefinancieerd is door de Nederlandse Organisatie voor Wetenschappelijk Onderzoek (NWO).

Ingevoerde data wordt verwerkt op de SURF research cloud, er wordt geen data opgeslagen.""")


# Create input in columns
def labeled_input(label, default):
    col1, col2 = st.columns([1, 2],vertical_alignment="center")
    with col1:
        st.markdown(f"<div style='padding-top: 8px'>{label}</div>", unsafe_allow_html=True)
    with col2:
        return st.text_input(label, label_visibility="hidden", value=str(default), key=label)

# Input helper
def get_number_input(label, default):
    input_str = labeled_input(label, default)
    input_str = input_str.replace(',', '.')
    if input_str.strip() == "":
        st.error(f"{label} is required.")
        return None
    try:
        return float(input_str)
    except ValueError:
        st.error(f"Invalid input for {label}. Please enter a number (e.g. 1.2 or 1,2).")
        return None

# PDF table helper
def add_table_to_pdf(pdf, df_table):
    pdf.set_font("Arial", size=10)
    col_width = 10
    row_height = 6
    
    
    marker=True
    while marker:
        if len(df_table.columns)>16:
            df_16 = df_table.iloc[:, 0:16]
            df_table = df_table.iloc[:, 16:]
        else:
            df_16 = df_table
            marker = False
        
        # Table columns (header)
        pdf.ln(5)
        pdf.set_fill_color(200, 200, 200)
        for col in df_16.columns: 
            pdf.cell(col_width, row_height, col, border=1, fill=True)
        pdf.ln(row_height)
    
        # Table rows
        for i in range(len(df_16)):
            for item in df_16.iloc[i]:
                formatted = f"{item:.1f}" if isinstance(item, float) else str(item)
                pdf.cell(col_width, row_height, formatted, border=1)
            pdf.ln(row_height)

# Main app
# maakt de witte randen wat kleiner
st.markdown("""
        <style>
               .block-container {
                    padding-top: 3rem;
                    padding-bottom: 10rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
        </style>
        """, unsafe_allow_html=True)

st.header(page_header)
st.write(introduction)

st.write(introduction_calculation)
st.write(introduction_input)

# Get input variabelen
soort_object = labeled_input(label_soort_object, "object")               #soort object
aantal_objecten = int(get_number_input(label_aantal_objecten, 230))                       # aantal fenders
gemiddelde_leefdtijd = get_number_input(label_gemiddelde_leefdtijd, 23.7)              # gemiddelde leefdtijd
stdev_leefdtijd = get_number_input(label_stdev_leefdtijd, 4.3)          # standaardafwijking
faalpercentage = get_number_input(label_faalpercentage, 0.33)            # percentage dat mag falen
if faalpercentage > 1:                                                          # check of faalpercentage als getal in procent is aangegeven, dan delen door 100 
    faalpercentage = faalpercentage/100

tijdshorizon = get_number_input(label_tijdshorizon, 100)                            # tijdsperiode die inzichtelijk moet worden gemaakt
vervangingskosten_object = get_number_input(label_vervangingskosten_object, 2)   # vervangingskosten fender
rentevoet = get_number_input(label_rentevoet, 0.02)                                 # discontovoet voor NCW berekening




pdf_bytes = None  # Placeholder for download

with st.container(border=True):
    
    st.write(disclaimer)

berekening = st.button("Berekening", type ="primary")

if berekening:
    if None in (aantal_objecten, gemiddelde_leefdtijd, stdev_leefdtijd, faalpercentage, tijdshorizon, vervangingskosten_object, rentevoet, N_sim):
        st.warning("Please fix the input errors above.")
    else:
        # Perform calculation
        n_vervangen, max_iteraties, fig, gem_vervangingstijden, kosten, totale_kosten, EAC = calc_group(aantal_objecten, gemiddelde_leefdtijd, stdev_leefdtijd, faalpercentage, tijdshorizon, vervangingskosten_object, rentevoet, N_sim)
        
        st.header("Resultaten")
        st.write(f"Omvang groepsvervanging: {n_vervangen} objecten")
        # st.write(f"Aantal iteraties: {max_iteraties}")
        
        # show plot on website
        st.pyplot(fig)
        
        # --- Toon de gemiddelde vervangingstijden als tabel ---
        st.write("Gemiddelde tijdstippen van groepsvervanging (jaren):  ")
        
        # table with data horizontal
        table_results = pd.DataFrame()
        tijdstippen = [f"t{i}" for i in range(1, len(kosten)+1)]
        table_results["Gemiddelde tijdstip per groepsvervanging"] = gem_vervangingstijden[:len(kosten)]
        #table_results["Verdisconteerde kosten voor jaar (in k€)"] = kosten
        table_results=table_results.transpose()
        table_results.columns = tijdstippen
        num_cols = table_results.select_dtypes(include=["float", "int"]).columns #find numeric columns
        # Create format dict with {:.1f} for numeric columns
        format_dict = {col: "{:.1f}" for col in num_cols}
        # disable options (download, etc) that appear when hovering over table
        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
                )
        
        st.dataframe(table_results.style.format(format_dict), hide_index="true", on_select="ignore", width="content")
        # st.write("""
        #           Gemiddelde tijdstippen van groepsvervanging (jaren):  """,
        #           table_results.style.format(format_dict), """  
        #           test
        #           """)
        
        if len(table_results.columns)>14:
            st.write("*Scroll in de tabel naar rechts voor meer resultaten* -->",)

        # Print de kosten en de totale som
        st.write(f"""
                 **Kosten**  
                 Totale som van verdisconteerde kosten voor {tijdshorizon:.0f} jaar: {totale_kosten:.1f} kEuro  
                 De Equivalente Jaarlijkse Kosten (EAC) gedurende {tijdshorizon:.0f} jaar: {EAC:.1f} kEuro""")
        
        
        ## Create PDF
        with st.spinner("Generating PDF..."):

           # Save plot to buffer
            img_buf = BytesIO()
            fig.savefig(img_buf, format='png')
            img_buf.seek(0)
    
            # Save image temporarily (fpdf requires file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                tmp_img.write(img_buf.read())
                plot_path = tmp_img.name
    
            # create pdf
            pdf = FPDF()
            pdf.set_left_margin(20)
            pdf.set_right_margin(20)
            pdf.set_top_margin(20)
            pdf.add_page()
            
            # Set font for the title
            pdf.set_font("Arial", "B", 16)
            pdf.multi_cell(0, 10, page_header, align="L")
    
            pdf.ln(5)  # add some vertical space
    
            # Set font for the body text
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 6, introduction)
    
            pdf.ln(5)  # space before inputs or plot
            
            pdf.multi_cell(0, 6, introduction_calculation)
            pdf.ln(5)
            pdf.multi_cell(0, 6, introduction_input, align="L")
            pdf.ln(3)  # space before inputs or plot
            
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, f"{label_soort_object}: {soort_object}", ln=True)
            pdf.cell(0, 8, f"{label_aantal_objecten}: {aantal_objecten}", ln=True)
            pdf.cell(0, 8, f"{label_gemiddelde_leefdtijd}: {gemiddelde_leefdtijd}", ln=True)
            pdf.cell(0, 8, f"{label_stdev_leefdtijd}: {stdev_leefdtijd}", ln=True)
            pdf.cell(0, 8, f"{label_faalpercentage}: {faalpercentage}", ln=True)
            pdf.cell(0, 8, f"{label_tijdshorizon}: {tijdshorizon}", ln=True)
            pdf.cell(0, 8, f"{label_vervangingskosten_object}: {vervangingskosten_object}", ln=True)
            pdf.cell(0, 8, f"{label_rentevoet}: {rentevoet}", ln=True)
            pdf.cell(0, 8, f"{label_N_sim}: {N_sim}", ln=True)
                        
            # add disclaimer
            pdf.ln(5)
            pdf.multi_cell(0, 6, disclaimer, align="L",border=1)
            
            #print resultaten
            pdf.set_font("Arial", "B", size=14)
            pdf.multi_cell(0, 6, "Resultaten")
            pdf.set_font("Arial", size=12)
            pdf.ln(5)
            pdf.multi_cell(0, 6, f"Omvang groepsvervanging: {n_vervangen} objecten")
            
            # Plot image
            pdf.ln(5)
            pdf.image(plot_path, x=10, w=180)
    
            # Add data table
            #pdf.add_page()
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Gemiddelde tijdstippen van groepsvervanging (jaren):", ln=True)
            add_table_to_pdf(pdf, table_results)
            
            #test table in plot

    
            # Export to bytes
            pdf_str = pdf.output(dest="S")   # get PDF as string
            pdf_bytes = pdf_str.encode("latin1")  # convert string to bytes

        # Download button
        ste.download_button(
            label="📄 Download PDF Rapport",
            data=pdf_bytes,
            file_name="berekening_groepsvervanging.pdf",
            mime="application/pdf"
        )
