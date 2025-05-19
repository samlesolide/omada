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
OMADA_SITE = config["OMADA_SITE"]
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]
ORIGINAL_SSID_NAME = config["ORIGINAL_SSID_NAME"]

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

HIDDEN_SSID_NAME = "PBA-Hidden"

def main():
    parser = argparse.ArgumentParser(description="Activer ou désactiver complètement le Wi-Fi (SSID) sur Omada Controller")
    parser.add_argument("action", choices=["enable", "disable"], help="Action à effectuer (enable = rendre visible, disable = masquer et renommer)")
    parser.add_argument("--host", default=OMADA_HOST, help=f"Hôte Omada (défaut: {OMADA_HOST})")
    parser.add_argument("--port", default=OMADA_PORT, help=f"Port Omada (défaut: {OMADA_PORT})")
    parser.add_argument("--site", default=OMADA_SITE, help=f"Nom du site Omada (défaut: {OMADA_SITE})")
    parser.add_argument("--debug", action="store_true", help="Activer le mode débogage")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    base_url = f"https://{args.host}:{args.port}"

    try:
        sys.path.append('omada-api')
        from omada.omada import Omada
        logger.info(f"Initialisation de la connexion à {base_url}...")
        omada = Omada(
            baseurl=base_url,
            site=args.site,
            verify=False,
            warnings=False
        )
        omada.session.verify = False
        logger.info("Connexion à l'API Omada...")
        omada.login(username=USERNAME, password=PASSWORD)
        logger.info("Connexion réussie")
        try:
            if args.action == "enable":
                set_ssid_broadcast_and_name(omada, enable=True)
            elif args.action == "disable":
                set_ssid_broadcast_and_name(omada, enable=False)
        finally:
            logger.info("Déconnexion de l'API Omada")
            omada.logout()
    except ImportError as e:
        logger.error(f"Erreur d'importation: {e}")
        logger.error("Assurez-vous que le module omada-api est accessible.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur: {e}")
        sys.exit(1)

def set_ssid_broadcast_and_name(omada, enable):
    """Active ou désactive le SSID en modifiant le champ broadcast, la bande et le pmfMode (le nom reste inchangé)"""
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
        # On cherche le SSID par son nom d'origine uniquement
        for group in wlan_groups:
            group_id = group.get('id')
            if group_id:
                ssid_endpoint = f"/sites/{site_id}/setting/wlans/{group_id}/ssids"
                ssid_result = omada._Omada__get(ssid_endpoint)
                if not ssid_result or 'data' not in ssid_result:
                    continue
                ssids = ssid_result['data']
                for ssid in ssids:
                    if ssid.get('name') == ORIGINAL_SSID_NAME:
                        target_ssid = ssid
                        target_group_id = group_id
                        break
            if target_ssid:
                break
        if not target_ssid:
            logger.error(f"SSID '{ORIGINAL_SSID_NAME}' non trouvé")
            return False
        ssid_id = target_ssid.get('id')
        if not ssid_id:
            logger.error("Impossible de récupérer l'ID du SSID")
            return False
        required_config = {k: v for k, v in target_ssid.items()}
        if enable:
            required_config['broadcast'] = True
            required_config['band'] = 3  # 2.4 + 5 GHz
            required_config['pmfMode'] = 2  # Optional
            action_desc = f"activé (visible, 2.4+5 GHz, pmf optional)"
        else:
            required_config['broadcast'] = False
            required_config['band'] = 4  # 6 GHz uniquement
            required_config['pmfMode'] = 1  # Mandatory
            action_desc = f"désactivé (masqué, 6 GHz, pmf mandatory)"
        logger.debug(f"Mise à jour du SSID (ID: {ssid_id}) dans le groupe {target_group_id}")
        logger.debug(f"Configuration envoyée: {json.dumps(required_config, indent=2)}")
        update_endpoint = f"/sites/{site_id}/setting/wlans/{target_group_id}/ssids/{ssid_id}"
        omada._Omada__patch(update_endpoint, json=required_config)
        print(f"SSID {action_desc} avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du SSID: {e}")
        return False

if __name__ == "__main__":
    main() 