from CpnDiscovery.Translator.translator import add_restrictions
from CpnDiscovery.discover_ocpn import convert_ocpn_to_cpn
from CpnDiscovery.Restrictions.restriction import *
from CpnDiscovery.MyCpn.CPN import *
from CpnDiscovery.discover_cardinalities import discover_optionality, get_object_frequencies, discover_narrow_variable_arcs, delete_zero_object_frequencies
from CpnDiscovery.o2o_sync import *
import pandas as pd
import pm4py

# evaluate computation time for different datasets for bound discovery, optionality discovery, sync discovery

# sync discovery -> with / witout ressource computation (pair comparisons can be interesting)
# ressource identification

# Cardinalities

# frequency map construction

# bound discovery
# - min-max vs IQR vs 

# ---------------------------
#
# --------------------------

# *Data Sets*
# Order-Management
# Container Logistics
# ?
# ? 
# ?
# - Activities
# - Events
# - Objects
# - Object Types
# - (Objects per Type)

# *Basic Steps*
# Load Dataset (takes often rather long)
# Discover OCPN (idk on the duration)
# convert OCPN to CPN

# *Discovery Steps*
# Frequency Map
# Discovery Bounded Var Arcs (minmax, IQR, quantiles(0.1), quantiles(0.3)) #4
# Discover Optionality (t=0, t=0.2) #2
# Discover Synchronization
# alpha (0, 0.2, 0.4, 0.6, 0.8, 1.0) #6
# beta (0, 0.2, 0.4, 0.6, 0.8, 1.0) #6

# *add restrictions*
# use restrictions from Discovery Steps


# detail synchronization evaluation


# Hypotheses
# Cardinality is very quick (Freq map is the longest part)
# optionality is very quick (Freq map is the longest part)
# Synchronization takes very long for o2a2 pairs if objects are involved in many events (ressource) (time corr evnets/object) (on either side)
# Synchronization takes longer if activities have many events (time corr events/activity)
# run synchronization without ressource identification 
# - count #objects ot1 #objects ot2 #activities a # activities b for every (ot1, ot2, a, b) set timeout to 1000s
# - compare against with and without ressource ident
# --> ressource identification


def main():
    datasets_stick = [
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/order-management.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_01_o2c.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_03_hiring.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_04_hospital.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/enron_top_100000.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/container_logistics.sqlite"
    ]
    datasets_laptop = [
        "/home/user/Documents/_MA/Data/order-management.sqlite",
        "/home/user/Documents/_MA/Data/container_logistics.sqlite"
    ]
    datasets = datasets_laptop
