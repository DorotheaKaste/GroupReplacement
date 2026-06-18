# -*- coding: utf-8 -*-
"""
Created on Sun Mar 30 11:19:51 2025

"""

import numpy as np
import matplotlib.pyplot as plt


# Definieer voorbeeld variabelen
aantal_objecten = 230                              # aantal objecten
gemiddelde_leefdtijd = 23.7                        # gemiddelde leefdtijd
stdev_leefdtijd = 4.3                              # standaardafwijking
# percentage dat mag falen in decimalen
faalpercentage = 1/3

# tijdsperiode die inzichtelijk moet worden gemaakt
tijdshorizon = 100

# vervangingskosten object in k€
vervangingskosten_object = 2

# discontovoet voor NCW berekening
rentevoet = 0.02

# Model variabelen
N_sim = 2000                                                # aantal simulaties


# hieronder alles in module
def calculate_group_replacements(aantal_objecten, gemiddelde_leefdtijd, stdev_leefdtijd, faalpercentage, tijdshorizon, vervangingskosten_object, rentevoet, N_sim):

    
    n_vervangen = int(aantal_objecten * faalpercentage)         # omvang groep
    # print(f"omvang groepsvervanging: {n_vervangen}")
    
    max_iteraties = int((tijdshorizon/gemiddelde_leefdtijd) *   # aantal iteraties
                        (aantal_objecten/n_vervangen))
    
    
    # Simuleer één scenario met groepsvervangingen voor periode T
    # Retouneert tijdstippen_falen_objecten_binnen cyclus (binnen omvang groep)
    # Retouneert tijdstippen_groepsvervanging
    
    def simuleer_uitval_groepsvervanging_objecten_scenario():
    
        #global aantal_objecten, gemiddelde_leefdtijd, stdev_leefdtijd, faalpercentage, max_iteraties, n_vervangen
    
        # Initieel falen genereren en sorteren
        faaltijden = np.sort(np.random.normal(
            gemiddelde_leefdtijd, stdev_leefdtijd, aantal_objecten))
    
        # Tijdstippen waarop de 1e, 2e, 3e, ..., max omvang falen, object uitvalt
        tijdstippen_falen_obecten_binnen_cyclus = []
        # Tijdstippen waarop groepsvervanging plaatsvindt
        tijdstippen_groepsvervanging = []
    
        for _ in range(max_iteraties):
            # Registreer tijdstippen van falende objecten binnen groep
            tijdstippen_falen_obecten_binnen_cyclus.append(
                faaltijden[:n_vervangen])
    
            # Bepaal het vervangingstijdstip t_vervanging_groep
            # d.w.z. wanneer het laatste object in een groep uitvalt
            t_vervanging_groep = faaltijden[n_vervangen - 1]
            tijdstippen_groepsvervanging.append(t_vervanging_groep)
    
            # Vervang de groep uitgevallen objecten door nieuwe met faaltijden vanaf t_vervanging_groep
            overgebleven = faaltijden[n_vervangen:]
            nieuwe_faaltijden = np.random.normal(
                gemiddelde_leefdtijd, stdev_leefdtijd, n_vervangen) + t_vervanging_groep
            faaltijden = np.sort(np.concatenate((overgebleven, nieuwe_faaltijden)))
    
        return np.array(tijdstippen_falen_obecten_binnen_cyclus), np.array(tijdstippen_groepsvervanging)
    
    
    # Monte Carlo simulatie voor het scenario met groepsvervangingen
    
    # Tijdstippen van 1e, 2e, 3e... uitval per cyclus (binnen groep en voor alle groepen)
    alle_tijdstippen_falen_obecten_binnen_cyclus = []
    alle_vervangingstijden = []  # Tijdstippen van groepsvervanging
    
    for _ in range(N_sim):
        tijdstippen_falen_obecten_binnen_cyclus, vervangingstijden = simuleer_uitval_groepsvervanging_objecten_scenario()
        alle_tijdstippen_falen_obecten_binnen_cyclus.append(
            tijdstippen_falen_obecten_binnen_cyclus)
        alle_vervangingstijden.append(vervangingstijden)
    
    # Omzetten naar arrays voor eenvoudig middelen
    alle_tijdstippen_falen_obecten_binnen_cyclus = np.array(
        alle_tijdstippen_falen_obecten_binnen_cyclus)
    alle_vervangingstijden = np.array(alle_vervangingstijden)
    
    # Gemiddelde uitvaltijden per cyclus (voor de objecten binnen een groep en voor alle groepen)
    gem_tijdstippen_falen_obecten_binnen_cyclus = np.mean(
        alle_tijdstippen_falen_obecten_binnen_cyclus, axis=0)
    gem_vervangingstijden = np.mean(alle_vervangingstijden, axis=0)
    
    
    # Zaagtand curve reconstrueren
    t_waarden = [0]  # Starttijd
    working_values = [aantal_objecten]  # Begin met aantal werkende objecten
    
    for cycle_idx in range(max_iteraties):
        for i in range(n_vervangen):  # objecten in groep vallen uit
            t_waarden.append(
                gem_tijdstippen_falen_obecten_binnen_cyclus[cycle_idx, i])
            working_values.append(aantal_objecten - (i + 1))
    
        # Groepsvervanging: spring terug naar oorspronkelijk aantal objecten
        t_vervanging_groep = gem_vervangingstijden[cycle_idx]
        t_waarden.append(t_vervanging_groep)
        working_values.append(aantal_objecten)
    
    # Plot de zaagtandcurve
    plt.figure(figsize=(12, 6))
    plt.step(t_waarden, working_values, where='post')
    
    
    plt.xlabel("Tijd (jaren)", fontsize=14)
    plt.ylabel("Aantal werkende objecten", fontsize=14)
    plt.title("Uitval en groepsvervangingen op basis van 2000 simulaties", fontsize=20)
    plt.grid()
    
    # Grid van gemiddelde levensduur op de x-as
    plt.xticks(np.arange(0, tijdshorizon+1, gemiddelde_leefdtijd))

    
    # Boven en onderwaarden voor x en y-as
    plt.xlim(0, tijdshorizon)

    # Berekening van netto contante waarde kosten_t(i) voor t < tijdshorizon jaar
    kosten = [(vervangingskosten_object*n_vervangen) / (1 + rentevoet)
              ** t for t in gem_vervangingstijden if t < tijdshorizon]
    
    # Som van alle kosten_t(i)
    totale_kosten = sum(kosten)

    
    # Berekening van Equivalent Annual Cost (EAC)
    EAC_factor = (rentevoet * (1 + rentevoet)**tijdshorizon) / \
        ((1 + rentevoet)**tijdshorizon - 1)
    EAC = totale_kosten * EAC_factor

    
    # return plot and values
    return n_vervangen, max_iteraties, plt, gem_vervangingstijden, kosten, totale_kosten, EAC