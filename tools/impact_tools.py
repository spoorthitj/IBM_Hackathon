"""Tools — Impact & Shelter Tools"""
from tools.registry import register_tool

def _get_population(query: str) -> str:
    return ("High-risk coastal population: Visakhapatnam 2.0M, Srikakulam 2.7M, "
            "Ganjam 3.5M, Puri 1.7M. Total at risk (50km coastal strip): ~12.4M")

def _get_shelter_list(query: str) -> str:
    return ("Active cyclone shelters: Srikakulam 62 (180k cap), "
            "Visakhapatnam 58 (145k cap), Ganjam 72 (220k cap), Puri 55 (165k cap). "
            "Total: 385 shelters, 8.2 lakh capacity.")

def _get_infrastructure(query: str) -> str:
    return ("Critical infrastructure at risk: HPCL Visakhapatnam Refinery, "
            "Gangavaram Port, NH-16 coastal stretch, 2 major power substations. "
            "Estimated downtime: 3-7 days post-landfall.")

def register():
    register_tool("get_population",     _get_population,    "Get population data for coastal districts","impact")
    register_tool("shelter_lookup",     _get_shelter_list,  "Look up cyclone shelter capacity",         "impact")
    register_tool("infrastructure_risk",_get_infrastructure,"Get critical infrastructure risk data",    "impact")
