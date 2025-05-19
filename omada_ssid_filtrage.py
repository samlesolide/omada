#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import logging
import json
import urllib3
import os
import ssl

# Forcer la non-vérification SSL au niveau de l'environnement
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Désactiver la vérification des certificats de façon globale
if hasattr(ssl, '_create_default_https_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# Charger la configuration depuis config.json
with open("config.json", "r") as f:
    config = json.load(f)
OMADA_HOST = config["OMADA_HOST"]
OMADA_PORT = config["OMADA_PORT"]
OMADA_BASEURL = f"https://{OMADA_HOST}:{OMADA_PORT}"
OMADA_SITE = config["OMADA_SITE"]
DEFAULT_SSID = config["DEFAULT_SSID"]
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]
MAC_FILTER_ID = config["MAC_FILTER_ID"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Désactiver les avertissements SSL pour requests
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Patcher l'objet Session pour toujours désactiver la vérification SSL
old_merge_environment_settings = requests.Session.merge_environment_settings

def merge_environment_settings(self, url, proxies, stream, verify, cert):
    settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
    settings['verify'] = False
    return settings
    
requests.Session.merge_environment_settings = merge_environment_settings

def main():
    parser = argparse.ArgumentParser(description="Contrôle des SSIDs sur Omada Controller")
    parser.add_argument("action", choices=["list", "enable", "disable"], help="Action à effectuer")
    parser.add_argument("--ssid", help=f"Nom du SSID à modifier (défaut: {DEFAULT_SSID})", default=DEFAULT_SSID)
    parser.add_argument("--host", default=OMADA_HOST, help=f"Hôte Omada (défaut: {OMADA_HOST})")
    parser.add_argument("--port", default=OMADA_PORT, help=f"Port Omada (défaut: {OMADA_PORT})")
    parser.add_argument("--site", default=OMADA_SITE, help=f"Nom du site Omada (défaut: {OMADA_SITE})")
    parser.add_argument("--debug", action="store_true", help="Activer le mode débogage")
    
    args = parser.parse_args()
    
    # Ajuster le niveau de journalisation si le mode debug est activé
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Mise à jour de l'URL si nécessaire
    base_url = f"https://{args.host}:{args.port}"
    
    # Initialiser la connexion à l'API Omada
    try:
        # Ajouter le chemin au module omada
        sys.path.append('omada-api')
        
        # Importer le module Omada
        from omada.omada import Omada
        
        # Créer l'instance Omada
        logger.info(f"Initialisation de la connexion à {base_url}...")
        omada = Omada(
            baseurl=base_url,
            site=args.site,
            verify=False,
            warnings=False
        )
        
        # Forcer la désactivation de la vérification SSL pour la session
        omada.session.verify = False
        
        # Connexion à l'API
        logger.info("Connexion à l'API Omada...")
        omada.login(username=USERNAME, password=PASSWORD)
        logger.info("Connexion réussie")
        
        try:
            if args.action == "list":
                list_wireless_networks(omada)
            
            elif args.action in ["enable", "disable"]:
                # Rechercher le SSID par son nom
                enable_state = args.action == "enable"
                logger.info(f"{'Activation' if enable_state else 'Désactivation'} du SSID '{args.ssid}'...")
                
                # Gestion du SSID
                change_ssid_state(omada, args.ssid, enable_state)
                
        finally:
            # Déconnexion
            logger.info("Déconnexion de l'API Omada")
            omada.logout()
            
    except ImportError as e:
        logger.error(f"Erreur d'importation: {e}")
        logger.error("Assurez-vous que le module omada-api est accessible.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur: {e}")
        sys.exit(1)

def list_wireless_networks(omada):
    """Liste tous les réseaux sans fil configurés"""
    logger.info("Récupération des groupes sans fil...")
    
    try:
        # Accès direct à l'API sans utiliser les générateurs
        site_id = omada._Omada__findKey()
        logger.debug(f"ID du site: {site_id}")
        
        # Récupérer les groupes WLAN directement
        wlan_endpoint = f"/sites/{site_id}/setting/wlans"
        wlan_result = omada._Omada__get(wlan_endpoint)
        
        # Vérifier que les données sont présentes
        if not wlan_result or 'data' not in wlan_result:
            logger.info("Aucun groupe sans fil trouvé")
            return
            
        wlan_groups = wlan_result['data']
        logger.info(f"Groupes sans fil trouvés: {len(wlan_groups)}")
        print("\nListe des réseaux sans fil configurés:")
        
        # Parcourir les groupes WLAN
        for group in wlan_groups:
            group_id = group.get('id')
            group_name = group.get('name')
            
            if not group_id or not group_name:
                continue
                
            logger.debug(f"Récupération des SSIDs pour le groupe '{group_name}' (ID: {group_id})...")
            
            # Récupérer les SSIDs pour ce groupe
            ssid_endpoint = f"/sites/{site_id}/setting/wlans/{group_id}/ssids"
            ssid_result = omada._Omada__get(ssid_endpoint)
            
            if not ssid_result or 'data' not in ssid_result:
                continue
                
            ssids = ssid_result['data']
            
            if ssids:
                print(f"\nGroupe: {group_name}")
                
                for ssid in ssids:
                    ssid_name = ssid.get('name', 'Sans nom')
                    ssid_id = ssid.get('id', '')
                    band_value = ssid.get('band', 0)
                    mac_filter_enabled = ssid.get('macFilterEnable', False)
                    mac_filter_type = ssid.get('macFilterType', 0)
                    mac_filter_list = ssid.get('macFilterList', [])
                    
                    # Déterminer les bandes actives
                    band_2g = bool(band_value & 1)    # bit 0 (binaire: 001)
                    band_5g = bool(band_value & 2)    # bit 1 (binaire: 010)
                    band_6g = bool(band_value & 4)    # bit 2 (binaire: 100)
                    
                    # Créer une chaîne pour les bandes actives
                    active_bands = []
                    if band_2g: active_bands.append("2.4GHz")
                    if band_5g: active_bands.append("5GHz")
                    if band_6g: active_bands.append("6GHz")
                    
                    # Information sur les bandes
                    bands_info = f"Bandes: {', '.join(active_bands) if active_bands else 'Aucune'}"
                    
                    # Information sur le filtrage MAC
                    if mac_filter_enabled:
                        if mac_filter_type == 0:
                            mac_filter_info = "Filtrage MAC: Activé (Interdiction)"
                        else:
                            mac_filter_info = "Filtrage MAC: Activé (Autorisation)"
                            
                        mac_count = len(mac_filter_list)
                        mac_filter_info += f" - {mac_count} appareil(s) dans la liste"
                        
                        # Si le filtrage est activé en mode autorisation et que la liste est vide,
                        # cela signifie qu'aucun appareil n'est autorisé (SSID effectivement désactivé)
                        if mac_filter_type == 1 and mac_count == 0:
                            mac_filter_info += " - SSID effectivement désactivé"
                    else:
                        mac_filter_info = "Filtrage MAC: Désactivé"
                    
                    # Afficher les informations
                    print(f"  - SSID: {ssid_name} (ID: {ssid_id})")
                    print(f"    {bands_info}")
                    print(f"    {mac_filter_info}")
                    
                    if logger.level == logging.DEBUG:
                        logger.debug(f"Détails du SSID: {json.dumps(ssid, indent=2)}")
                        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des réseaux sans fil: {e}")

def change_ssid_state(omada, ssid_name, enable):
    """Active ou désactive un réseau sans fil par son nom en utilisant le filtrage MAC (version finale, macFilterId en dur)"""
    try:
        site_id = omada._Omada__findKey()
        logger.debug(f"ID du site: {site_id}")
        wlan_endpoint = f"/sites/{site_id}/setting/wlans"
        wlan_result = omada._Omada__get(wlan_endpoint)
        if not wlan_result or 'data' not in wlan_result:
            logger.error("Aucun groupe sans fil trouvé")
            return False
        wlan_groups = wlan_result['data']
        target_ssid = None
        target_group_id = None
        for group in wlan_groups:
            group_id = group.get('id')
            if group_id:
                ssid_endpoint = f"/sites/{site_id}/setting/wlans/{group_id}/ssids"
                ssid_result = omada._Omada__get(ssid_endpoint)
                if not ssid_result or 'data' not in ssid_result:
                    continue
                ssids = ssid_result['data']
                for ssid in ssids:
                    if ssid.get('name') == ssid_name:
                        target_ssid = ssid
                        target_group_id = group_id
                        break
            if target_ssid:
                break
        if not target_ssid:
            logger.error(f"SSID '{ssid_name}' non trouvé")
            return False
        ssid_id = target_ssid.get('id')
        if not ssid_id:
            logger.error("Impossible de récupérer l'ID du SSID")
            return False
        if enable:
            required_config = {k: v for k, v in target_ssid.items()}
            required_config['macFilterEnable'] = False
            for key in ['macFilterList', 'macFilterType', 'policy', 'macFilterId']:
                if key in required_config:
                    del required_config[key]
            action_desc = "activé (filtrage MAC désactivé)"
        else:
            required_config = {k: v for k, v in target_ssid.items()}
            required_config['macFilterEnable'] = True
            required_config['policy'] = 1
            required_config['macFilterType'] = 1
            required_config['macFilterList'] = []
            required_config['macFilterId'] = MAC_FILTER_ID
            action_desc = "désactivé (filtrage MAC activé en mode autorisation uniquement, macFilterList vide, macFilterId en dur)"
        logger.debug(f"Mise à jour du SSID '{ssid_name}' (ID: {ssid_id}) dans le groupe {target_group_id}")
        logger.debug(f"Configuration envoyée: {json.dumps(required_config, indent=2)}")
        update_endpoint = f"/sites/{site_id}/setting/wlans/{target_group_id}/ssids/{ssid_id}"
        omada._Omada__patch(update_endpoint, json=required_config)
        print(f"SSID '{ssid_name}' {action_desc} avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du SSID: {e}")
        return False

if __name__ == "__main__":
    main() 