# Omada Controller API Control

Scripts Python pour contrôler et gérer les SSID d'un contrôleur TP-Link Omada via son API REST.

## Fonctionnalités

- ✅ Authentification automatique au contrôleur Omada
- ✅ Affichage de la liste des SSID Wi-Fi configurés avec leurs détails
- ✅ Activation/désactivation des SSID via le filtrage MAC (`omada_ssid_filtrage.py`)
- ✅ Activation/désactivation complète du Wi-Fi d'un SSID (bascule de bande, PMF, broadcast) (`omada_ssid_main.py`)

## Prérequis

- Python 3.6 ou supérieur
- Module `requests` installé
- Bibliothèque `omada-api` (incluse dans le dossier `omada-api`)
- Un contrôleur Omada TP-Link (testé sur la version 5.15.20.20)
- Accès administrateur au contrôleur Omada
- L'API OpenAPI activée dans l'interface web du contrôleur

## Installation

1. Clonez ou téléchargez ce dépôt
2. Installez les dépendances requises :

```
pip install -r requirements.txt
```

3. Modifiez les paramètres dans les scripts pour correspondre à votre environnement :

**Exemple pour `omada_ssid_filtrage.py`** :
```python
OMADA_HOST = "192.168.1.42"
OMADA_PORT = "8043"
OMADA_SITE = "Petit-Bel-Air"
DEFAULT_SSID = "Petit-Bel-Air"
USERNAME = "votre_nom_utilisateur"
PASSWORD = "votre_mot_de_passe"
MAC_FILTER_ID = "682a3ad07f5cbf2ca260b9ad"  # À adapter selon votre SSID
```

**Exemple pour `omada_ssid_main.py`** :
```python
OMADA_HOST = "192.168.1.42"
OMADA_PORT = "8043"
OMADA_SITE = "Petit-Bel-Air"
USERNAME = "votre_nom_utilisateur"
PASSWORD = "votre_mot_de_passe"
ORIGINAL_SSID_NAME = "Petit-Bel-Air"
```

## Configuration

Avant d'utiliser les scripts, créez un fichier `config.json` à la racine du projet avec le contenu suivant (adaptez les valeurs à votre environnement) :

```json
{
  "OMADA_HOST": "192.168.1.42",
  "OMADA_PORT": "8043",
  "OMADA_SITE": "Petit-Bel-Air",
  "USERNAME": "votre_nom_utilisateur",
  "PASSWORD": "votre_mot_de_passe",
  "DEFAULT_SSID": "Petit-Bel-Air",
  "MAC_FILTER_ID": "682a3ad07f5cbf2ca260b9ad",
  "ORIGINAL_SSID_NAME": "Petit-Bel-Air"
}
```

> ⚠️ **Ne versionnez pas ce fichier si vous stockez des identifiants sensibles. Ajoutez-le à votre `.gitignore` si besoin.**

Les scripts `omada_ssid_filtrage.py` et `omada_ssid_main.py` liront automatiquement la configuration depuis ce fichier.

## Utilisation

### 1. Contrôle des SSID via filtrage MAC (`omada_ssid_filtrage.py`)

Lister les SSID configurés :
```
python omada_ssid_filtrage.py list
```

Activer un SSID (rendre le Wi-Fi accessible à tous) :
```
python omada_ssid_filtrage.py enable --ssid "Nom_du_SSID"
```

Désactiver un SSID (rendre le Wi-Fi inaccessible à tous) :
```
python omada_ssid_filtrage.py disable --ssid "Nom_du_SSID"
```

Afficher des informations de débogage détaillées :
```
python omada_ssid_filtrage.py list --debug
```

### 2. Activation/désactivation complète du Wi-Fi d'un SSID (`omada_ssid_main.py`)

Ce script permet d'activer ou de désactiver complètement le Wi-Fi d'un SSID sans changer son nom, en modifiant uniquement :
- Les bandes actives (2.4+5 GHz pour activer, 6 GHz seul pour désactiver)
- Le mode PMF (2 = Optional pour activer, 1 = Mandatory pour désactiver)
- Le broadcast (True pour activer, False pour désactiver)

Désactiver complètement le Wi-Fi (SSID masqué, 6 GHz seul, PMF mandatory) :
```
python omada_ssid_main.py disable
```

Réactiver le Wi-Fi (SSID visible, 2.4+5 GHz, PMF optional) :
```
python omada_ssid_main.py enable
```

## Gestion du champ macFilterId

- **macFilterId** est un identifiant unique associé au filtrage MAC d'un SSID.
- Il est indispensable de le renseigner dans le script `omada_ssid_filtrage.py` pour que la désactivation fonctionne.
- Vous pouvez obtenir ce champ en listant les SSID alors que le filtrage MAC est activé (voir debug du script).
- Le macFilterId reste le même pour un SSID donné, même après désactivation/réactivation du filtrage MAC.
- Si vous contrôlez plusieurs SSID, ajoutez une variable `MAC_FILTER_ID` pour chacun.

## Implémentation technique

### 1. Filtrage MAC (`omada_ssid_filtrage.py`)
- **Activation d'un SSID** : désactive le filtrage MAC (`macFilterEnable = False`).
- **Désactivation d'un SSID** : active le filtrage MAC (`macFilterEnable = True`), en mode autorisation (`policy = 1`, `macFilterType = 1`) avec une liste vide (`macFilterList = []`) et le bon `macFilterId`.
- Le script gère automatiquement la structure de la requête PATCH pour l'API Omada.

### 2. Bascule de bande/broadcast (`omada_ssid_main.py`)
- **Activation** : `band = 3` (2.4 + 5 GHz), `pmfMode = 2` (Optional), `broadcast = True`
- **Désactivation** : `band = 4` (6 GHz uniquement), `pmfMode = 1` (Mandatory), `broadcast = False`

### Endpoints API utilisés
- `/sites/{siteId}/setting/wlans` - Pour lister les groupes WLAN
- `/sites/{siteId}/setting/wlans/{wlanId}/ssids` - Pour lister les SSID dans chaque groupe
- `/sites/{siteId}/setting/wlans/{wlanId}/ssids/{ssidId}` - Pour modifier un SSID (PATCH)

## Certificats SSL

Les scripts désactivent par défaut la vérification SSL pour faciliter l'utilisation avec des certificats auto-signés. Pour une utilisation en production, il est recommandé d'utiliser des certificats valides et d'activer la vérification SSL.

## Dépannage

- Activez le mode debug avec `--debug` pour voir les détails des requêtes et réponses API
- Vérifiez que l'API est bien activée dans l'interface web du contrôleur Omada
- Vérifiez que les identifiants, l'URL du contrôleur et le `macFilterId` sont corrects
- Assurez-vous que le contrôleur Omada est accessible depuis la machine où le script est exécuté

## Auteur

Scripts créés pour contrôler un réseau Wi-Fi domestique via Omada Controller.

## API HTTP locale pour pilotage à distance

Pour permettre à Home Assistant (ou tout autre système) de piloter les scripts à distance, un micro-serveur Flask est fourni : `omada_api_server.py`.

### Installation

1. Installez Flask sur le serveur Omada :
   ```bash
   pip install flask
   ```
2. Lancez le serveur :
   ```bash
   python3 omada_api_server.py
   ```
   (Vous pouvez utiliser un service systemd ou tmux/screen pour le garder actif en arrière-plan.)

### Endpoints disponibles

- **Activer/Désactiver le Wi-Fi principal**
  - `POST /wifi/enable`  → Active le Wi-Fi (bascule de bande)
  - `POST /wifi/disable` → Désactive le Wi-Fi (bascule de bande)

- **Contrôle d'un SSID par filtrage MAC**
  - `POST /ssid/enable`  → Active un SSID (optionnel : JSON `{"ssid": "NomDuSSID"}`)
  - `POST /ssid/disable` → Désactive un SSID (optionnel : JSON `{"ssid": "NomDuSSID"}`)
  - `POST /ssid/list`    → Liste les SSID

### Exemples d'appel (curl)

```bash
curl -X POST http://IP_OMADA:5005/wifi/enable
curl -X POST http://IP_OMADA:5005/ssid/disable -H "Content-Type: application/json" -d '{"ssid": "NomDuSSID"}'
curl -X POST http://IP_OMADA:5005/ssid/list
```

### Intégration Home Assistant (exemple)

Dans `configuration.yaml` :
```yaml
rest_command:
  omada_wifi_enable:
    url: "http://IP_OMADA:5005/wifi/enable"
    method: POST
  omada_wifi_disable:
    url: "http://IP_OMADA:5005/wifi/disable"
    method: POST
  omada_ssid_enable:
    url: "http://IP_OMADA:5005/ssid/enable"
    method: POST
    content_type: 'application/json'
    payload: '{"ssid": "NomDuSSID"}'
  omada_ssid_disable:
    url: "http://IP_OMADA:5005/ssid/disable"
    method: POST
    content_type: 'application/json'
    payload: '{"ssid": "NomDuSSID"}'
  omada_ssid_list:
    url: "http://IP_OMADA:5005/ssid/list"
    method: POST
```

Vous pouvez ensuite utiliser ces commandes dans vos automatisations, scripts ou boutons Home Assistant.

> ⚠️ L'API n'a pas d'authentification par défaut. Restreignez l'accès réseau si besoin (firewall, VLAN, etc.).

### Faire tourner l'API en permanence avec `systemd` (sur Raspberry Pi / Linux)

Pour que le serveur API Flask (`omada_api_server.py`) s'exécute en continu en arrière-plan et redémarre automatiquement avec le système, il est recommandé de le configurer comme un service `systemd`.

1.  **Créez un fichier de service `systemd` :**
    Ouvrez un nouveau fichier de service avec `nano` ou votre éditeur préféré :
    ```bash
    sudo nano /etc/systemd/system/omada-api.service
    ```

2.  **Collez la configuration suivante dans le fichier :**
    Assurez-vous d'adapter `User`, `Group`, `WorkingDirectory`, et `ExecStart` si votre nom d'utilisateur ou le chemin vers le projet est différent. Les chemins doivent être absolus.

    ```ini
    [Unit]
    Description=Omada API Flask Server
    After=network.target

    [Service]
    User=pi
    Group=pi
    WorkingDirectory=/home/pi/omada/omada-tools # Adaptez ce chemin si nécessaire
    ExecStart=/home/pi/omada/omada-tools/venv/bin/python /home/pi/omada/omada-tools/omada_api_server.py # Adaptez ce chemin si nécessaire
    Restart=always
    Environment="PYTHONUNBUFFERED=1"

    [Install]
    WantedBy=multi-user.target
    ```

    *   `User` et `Group` : L'utilisateur sous lequel le service s'exécutera (généralement `pi` sur un Raspberry Pi).
    *   `WorkingDirectory` : Le chemin absolu vers le dossier où se trouvent vos scripts (`omada_api_server.py`, `config.json`, etc.) et le dossier `venv`.
    *   `ExecStart` : Le chemin absolu vers l'interpréteur Python de votre environnement virtuel (`venv/bin/python`) suivi du chemin absolu vers votre script `omada_api_server.py`.

3.  **Sauvegardez et fermez le fichier** (Ctrl+X, puis Y, puis Entrée dans `nano`).

4.  **Rechargez la configuration de `systemd` :**
    Pour que `systemd` prenne en compte le nouveau service.
    ```bash
    sudo systemctl daemon-reload
    ```

5.  **Activez le service pour qu'il démarre au boot :**
    ```bash
    sudo systemctl enable omada-api.service
    ```

6.  **Démarrez le service :**
    ```bash
    sudo systemctl start omada-api.service
    ```

7.  **Vérifiez l'état du service :**
    ```bash
    sudo systemctl status omada-api.service
    ```
    Vous devriez voir `active (running)`. Si ce n'est pas le cas, utilisez `sudo journalctl -u omada-api.service -b` pour voir les logs et diagnostiquer les erreurs.

8.  **Pour consulter les logs du service plus tard :**
    ```bash
    sudo journalctl -u omada-api.service # Voir tous les logs
    sudo journalctl -f -u omada-api.service # Suivre les logs en temps réel
    ```

Avec ces étapes, votre API Omada sera gérée par `systemd` et fonctionnera de manière fiable en arrière-plan. 