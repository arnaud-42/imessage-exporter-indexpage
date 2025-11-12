import sys, os, re, html, argparse
from datetime import datetime
import json
from html.parser import HTMLParser

class ChatHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_timestamp_span = False
        self.in_anchor = False
        self.timestamps = []
        self.in_sender_span = False
        self.senders = []
        self.in_bubble_span = False
        self.all_messages_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "span" and attrs.get("class") == "timestamp":
            self.in_timestamp_span = True
        if tag == "a" and self.in_timestamp_span:
            self.in_anchor = True
        if tag == "span" and attrs.get("class") == "sender":
            self.in_sender_span = True
        if tag == "span" and attrs.get("class") == "bubble":
            self.in_bubble_span = True

    def handle_endtag(self, tag):
        if tag == "a" and self.in_anchor:
            self.in_anchor = False
        if tag == "span":
            if self.in_timestamp_span:
                self.in_timestamp_span = False
            if self.in_sender_span:
                self.in_sender_span = False
            if self.in_bubble_span:
                self.in_bubble_span = False

    def handle_data(self, data):
        if self.in_anchor and self.in_timestamp_span:
            txt = data.strip()
            if txt:
                self.timestamps.append(txt)
        if self.in_sender_span:
            txt = data.strip()
            if txt:
                self.senders.append(txt)
        if self.in_bubble_span:
            txt = data.strip()
            if txt:
                self.all_messages_text.append(txt)


DATE_PATTERNS = [
    "%b %d, %Y %I:%M:%S %p",
    "%b %d, %Y %I:%M %p",
    "%Y-%m-%d %H:%M:%S",
    "%d %b %Y %H:%M:%S",
    "%d %b %Y %H:%M"
]

# Dictionnaire de localisation
LOCALIZATION = {
    "fr": {
        "title": "Index des contacts",
        "intro": "Clique sur un en-tête pour trier les colonnes.",
        "search_placeholder": "Recherche texte ou contact...",
        "scope_label": "Portée :",
        "scope_name": "Contact",
        "scope_message": "Messages",
        "date_start_label": "Date de début:",
        "date_end_label": "Date de fin:",
        "fuzzy_label": "Recherche approximative (Fuzzy)",
        "col_contact": "Contact",
        "col_last_contact": "Dernier contact",
        "col_messages": "Messages",
        "col_preview": "Aperçu",
        "lang_fr": "Français",
        "lang_en": "English",
        "lang_note": "La langue a été mise à jour.",
        "search_fuzzy": " (Fuzzy)" # Pour la traduction des aperçus dynamiques
    },
    "en": {
        "title": "Contacts Index",
        "intro": "Click on a header to sort the columns.",
        "search_placeholder": "Search text or contact...",
        "scope_label": "Scope:",
        "scope_name": "Contact",
        "scope_message": "Messages",
        "date_start_label": "Start Date:",
        "date_end_label": "End Date:",
        "fuzzy_label": "Fuzzy Search",
        "col_contact": "Contact",
        "col_last_contact": "Last Contact",
        "col_messages": "Messages",
        "col_preview": "Preview",
        "lang_fr": "Français",
        "lang_en": "English",
        "lang_note": "Language updated.",
        "search_fuzzy": " (Fuzzy)"
    }
}

def normalize_spaces(s: str) -> str:
    s = re.sub(r'[\ufeff\u200b\u200c]', '', s)
    return re.sub(r"\s+", " ", s.strip())

def parse_dt(s: str):
    s_norm = normalize_spaces(s)
    for pat in DATE_PATTERNS:
        try:
            return datetime.strptime(s_norm, pat)
        except ValueError:
            continue
    return None

def guess_contact_name(filename_stem: str, senders: list):
    for s in senders:
        if s.lower() != "me":
            return s
    return filename_stem

def scan_file(path: str):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return None

    parser = ChatHTMLParser()
    parser.feed(content)

    dts = [parse_dt(t) for t in parser.timestamps if parse_dt(t)]
    if not dts:
        return None

    last_dt = max(dts)
    msg_count = len(dts)
    stem = os.path.splitext(os.path.basename(path))[0]
    name = guess_contact_name(stem, parser.senders)
    
    serial_messages_data = []
    all_messages_text_list = []
    
    num_messages = min(len(parser.timestamps), len(parser.all_messages_text))

    for i in range(num_messages):
        text = normalize_spaces(parser.all_messages_text[i]).lower() 
        dt = parse_dt(parser.timestamps[i])

        if dt and text:
            serial_messages_data.append({
                "ts": dt.timestamp(),
                "date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "text": text
            })
            all_messages_text_list.append(text)

    full_serial_string = json.dumps(serial_messages_data, ensure_ascii=False)

    return {
        "file": os.path.basename(path),
        "name": name,
        "last_contact": last_dt,
        "messages": msg_count,
        "all_messages_text": " ".join(all_messages_text_list), 
        "serial_messages": full_serial_string 
    }

def build_index(entries, output_path: str, lang="fr"):
    entries.sort(key=lambda x: x["last_contact"], reverse=True)
    rows = []
    
    texts = LOCALIZATION.get(lang, LOCALIZATION["fr"]) 
    
    # 1. Préparer les données de localisation complètes pour le JS
    json_localization = json.dumps(LOCALIZATION, ensure_ascii=False)
    
    for e in entries:
        date_str = e["last_contact"].strftime("%Y-%m-%d %H:%M:%S")
        rows.append(f"""
        <tr data-contact-search="{html.escape(e['name'].lower())}" 
            data-raw-messages="{html.escape(e['serial_messages'])}"
            data-messages-content="{html.escape(e['all_messages_text'])}">
          <td data-original-name="{html.escape(e['name'])}"><a href="{html.escape(e['file'])}" target="_blank">{html.escape(e['name'])}</a></td>
          <td class="nowrap" data-timestamp="{e['last_contact'].timestamp()}">{html.escape(date_str)}</td>
          <td>{e['messages']}</td>
          <td class="search-preview-cell preview-column"><div class="search-preview"></div></td>
        </tr>
        """)
        
    # 2. Sélecteur de langue mis à jour pour appeler la fonction JS
    lang_selector = f"""
    <div id="lang-selector-container">
        <label for="lang-select">Langue :</label>
        <select id="lang-select" onchange="changeLanguage(this.value)">
            <option value="fr" {'selected' if lang == 'fr' else ''}>{texts['lang_fr']}</option>
            <option value="en" {'selected' if lang == 'en' else ''}>{texts['lang_en']}</option>
        </select>
    </div>
    """
    
    html_doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(texts["title"])}</title>
<style>
  /* Toutes les accolades de style sont échappées: {{ et }} */
  body {{ 
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; 
      margin: 24px; 
  }}
  h1 {{ margin-bottom: 0.2rem; }}
  .muted {{ color: #666; margin-top: 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }}
  th {{ cursor: pointer; background: #f3f4f6; user-select: none; }}
  tr:hover {{ background: #f9fafb; }}
  .small {{ font-size: .9rem; }}
  .asc::after {{ content: " ▲"; }}
  .desc::after {{ content: " ▼"; }}
  /* Styles pour le sélecteur de langue */
  #lang-selector-container {{ margin-bottom: 20px; }}
  #lang-select {{ padding: 5px; border: 1px solid #ccc; border-radius: 4px; }}
  #lang-note {{ font-size: 0.8em; color: green; margin-top: 5px; display: none; }}

  #search-container input[type="text"] {{ padding: 8px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; width: 300px; }}
  #search-container input[type="date"] {{ padding: 8px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; width: 150px; }}
  #search-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
  #scope-toggle-container {{ border: 1px solid #ddd; padding: 7px; border-radius: 4px; font-size: 0.9em; }}
  #scope-toggle-container label {{ margin-right: 15px; white-space: nowrap; }}
  .nowrap {{ white-space: nowrap; }} 
  .search-preview-cell {{ font-size: 0.9em; max-width: 400px; }}
  .preview-date {{ 
      display: block; 
      font-size: 0.8em; 
      color: #666; 
      margin-bottom: 2px;
      font-style: italic;
  }}
  .search-preview strong, td strong {{ color: #C00; font-weight: bold; background-color: #ffe0e0; padding: 1px 0; border-radius: 2px; }}
  .snippet-separator {{ 
      border-top: 1px dashed #ddd; 
      margin: 5px 0; 
      height: 0; 
  }}
  
  /* Masque la colonne d'aperçu par défaut */
  #preview-header, .preview-column {{
      display: none;
  }}
</style>

<div style="display: flex; justify-content: space-between; align-items: flex-end;">
    <h1 id="main-title">{html.escape(texts["title"])}</h1>
    <div>
        {lang_selector}
        <div id="lang-note" class="small">{texts["lang_note"]}</div>
    </div>
</div>

<p class="muted small" id="intro-text">{html.escape(texts["intro"])}</p>

<div id="search-container">
    <input type="text" id="search-input" placeholder="{html.escape(texts["search_placeholder"])}" onkeyup="debounceSearch()">
    
    <div id="scope-toggle-container">
        <label id="scope-label-text">{html.escape(texts["scope_label"])}</label>
        <label>
            <input type="checkbox" id="scope-name" checked onchange="debounceSearch()">
            <span id="scope-name-text">{html.escape(texts["scope_name"])}</span>
        </label>
        <label>
            <input type="checkbox" id="scope-message" checked onchange="debounceSearch()">
            <span id="scope-message-text">{html.escape(texts["scope_message"])}</span>
        </label>
    </div>

    <div>
        <label for="date-start" id="date-start-label-text">{html.escape(texts["date_start_label"])}</label>
        <input type="date" id="date-start" onchange="debounceSearch()">
    </div>
    
    <div>
        <label for="date-end" id="date-end-label-text">{html.escape(texts["date_end_label"])}</label>
        <input type="date" id="date-end" onchange="debounceSearch()">
    </div>
    
    <div id="fuzzy-toggle-container">
        <label>
            <input type="checkbox" id="fuzzy-toggle" checked onchange="debounceSearch()">
            <span id="fuzzy-label-text">{html.escape(texts["fuzzy_label"])}</span>
        </label>
    </div>
</div>

<table id="contactsTable">
  <thead>
    <tr>
      <th data-type="text" id="col-contact-header">{html.escape(texts["col_contact"])}</th>
      <th data-type="date" id="col-last-contact-header">{html.escape(texts["col_last_contact"])}</th>
      <th data-type="num" id="col-messages-header">{html.escape(texts["col_messages"])}</th>
      <th data-type="text" id="preview-header" class="preview-column">{html.escape(texts["col_preview"])}</th>
    </tr>
  </thead>
  <tbody>
    {''.join(rows)}
  </tbody>
</table>

<script>
// --- NOUVEAU: Données de localisation injectées par Python ---
const ALL_LOCALIZATION_DATA = JSON.parse('{json_localization}');
let currentLang = '{lang}';
// ---

let searchTimeout = null;
const SEARCH_DELAY = 300; 

function changeLanguage(newLang) {{
    if (!ALL_LOCALIZATION_DATA[newLang]) return;

    currentLang = newLang;
    const texts = ALL_LOCALIZATION_DATA[newLang];
    
    // 1. Mise à jour des balises simples
    document.getElementById('main-title').textContent = texts.title;
    document.getElementById('intro-text').textContent = texts.intro;
    document.getElementById('search-input').placeholder = texts.search_placeholder;

    // 2. Mise à jour des labels
    document.getElementById('scope-label-text').textContent = texts.scope_label;
    document.getElementById('scope-name-text').textContent = texts.scope_name;
    document.getElementById('scope-message-text').textContent = texts.scope_message;
    document.getElementById('date-start-label-text').textContent = texts.date_start_label;
    document.getElementById('date-end-label-text').textContent = texts.date_end_label;
    document.getElementById('fuzzy-label-text').textContent = texts.fuzzy_label;
    
    // 3. Mise à jour des en-têtes de colonnes
    document.getElementById('col-contact-header').textContent = texts.col_contact;
    document.getElementById('col-last-contact-header').textContent = texts.col_last_contact;
    document.getElementById('col-messages-header').textContent = texts.col_messages;
    document.getElementById('preview-header').textContent = texts.col_preview;
    
    // 4. Mise à jour de l'attribut lang
    document.documentElement.lang = newLang;
    
    // 5. Afficher une note de confirmation (si besoin) et re-filtrer (pour traduire le "Fuzzy" dans l'aperçu)
    // Cacher après 2 secondes
    const langNote = document.getElementById('lang-note');
    langNote.textContent = texts.lang_note;
    langNote.style.display = 'block';
    setTimeout(() => {{ langNote.style.display = 'none'; }}, 2000);
    
    // Si la barre de recherche est active, le re-filtrage mettra à jour la traduction des aperçus dynamiques (e.g. "Fuzzy")
    if (document.getElementById('search-input').value.length > 0) {{
        filterTable();
    }}
}}

// --- Fonctions de recherche et de tri (largement inchangées, mais avec traduction du "Fuzzy") ---

function getLevenshteinDistance(a, b) {{
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;

  const matrix = [];

  for (let i = 0; i <= b.length; i++) {{
    matrix[i] = [i];
  }}

  for (let j = 0; j <= a.length; j++) {{
    matrix[0][j] = j;
  }}

  for (let i = 1; i <= b.length; i++) {{
    for (let j = 1; j <= a.length; j++) {{
      if (b.charAt(i - 1) === a.charAt(j - 1)) {{
        matrix[i][j] = matrix[i - 1][j - 1];
      }} else {{
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          Math.min(
            matrix[i][j - 1] + 1, // insertion
            matrix[i - 1][j] + 1  // deletion
          )
        );
      }}
    }}
  }}

  return matrix[b.length][a.length];
}}

function fuzzyMatch(text, filter) {{
    if (text.indexOf(filter) > -1) return true; 

    if (filter.length < 4) return false; 
    
    const distance = getLevenshteinDistance(text, filter);
    
    const max_allowed_distance = Math.floor(filter.length / 5) + 1; 

    return distance <= max_allowed_distance;
}}

function initializeTable() {{
    const tr = document.getElementById('contactsTable').getElementsByTagName('tr');
    for (let i = 0; i < tr.length; i++) {{ 
        const tr_element = tr[i];
        if (tr_element.hasAttribute('data-raw-messages')) {{
            try {{
                const rawJson = tr_element.getAttribute('data-raw-messages');
                tr_element.messagesData = JSON.parse(rawJson); 
                tr_element.removeAttribute('data-raw-messages'); 
            }} catch (e) {{
                console.error("Erreur lors du parsing des messages pour la ligne:", i, e);
                tr_element.messagesData = []; 
            }}
        }}
    }}
}}
window.addEventListener('load', initializeTable);


function debounceSearch() {{
    clearTimeout(searchTimeout); 
    searchTimeout = setTimeout(() => {{ 
        filterTable(); 
    }}, SEARCH_DELAY);
}}

document.querySelectorAll("th").forEach(th => th.addEventListener("click", () => {{
    const table = th.closest("table");
    const tbody = table.querySelector("tbody");
    const type = th.dataset.type;
    const index = Array.from(th.parentNode.children).indexOf(th);
    const currentOrder = th.classList.contains("asc") ? "asc" : th.classList.contains("desc") ? "desc" : null;

    document.querySelectorAll("th").forEach(h => h.classList.remove("asc", "desc"));
    const newOrder = currentOrder === "asc" ? "desc" : "asc";
    th.classList.add(newOrder);

    const rows = Array.from(tbody.querySelectorAll("tr"));
    rows.sort((a, b) => {{ 
        let A = a.children[index].innerText.trim();
        let B = b.children[index].innerText.trim();

        if (type === "num") {{ 
            A = parseInt(A) || 0;
            B = parseInt(B) || 0;
            return newOrder === "asc" ? A - B : B - A;
        }}
        if (type === "date") {{ 
            A = parseFloat(a.children[index].dataset.timestamp) || 0;
            B = parseFloat(b.children[index].dataset.timestamp) || 0;
            return newOrder === "asc" ? A - B : B - A;
        }}
        // text
        return newOrder === "asc" ? A.localeCompare(B) : B.localeCompare(A);
    }});
    rows.forEach(r => tbody.appendChild(r));
}})); 

function dateToTimestamp(dateString) {{
    if (!dateString) return null;
    const dt = new Date(dateString + 'T00:00:00'); 
    return dt.getTime() / 1000; 
}}

function filterTable() {{ 
    const texts = ALL_LOCALIZATION_DATA[currentLang]; // Traduction dynamique
    const input = document.getElementById('search-input');
    const filter = input.value.toLowerCase().trim();
    const tr = document.getElementById('contactsTable').getElementsByTagName('tr');
    
    // ... (Récupération des filtres inchangée)
    const dateStart = document.getElementById('date-start').value;
    const dateEnd = document.getElementById('date-end').value;
    const tsStart = dateToTimestamp(dateStart);
    const tsEnd = dateToTimestamp(dateEnd) ? dateToTimestamp(dateEnd) + 86400 : null; 
    const isFuzzyEnabled = document.getElementById('fuzzy-toggle').checked;
    
    const scopeName = document.getElementById('scope-name').checked;
    const scopeMessage = document.getElementById('scope-message').checked;

    const filterActive = filter.length > 0 || tsStart !== null || tsEnd !== null;

    const previewColumns = document.querySelectorAll('.preview-column');
    if (filter.length > 0 && scopeMessage) {{ 
        previewColumns.forEach(el => el.style.display = 'table-cell');
    }} else {{
        previewColumns.forEach(el => el.style.display = 'none');
    }}

    // ... (Réinitialisation si filtre inactif inchangée)
    if (!filterActive) {{ 
        for (let i = 0; i < tr.length; i++) {{ 
            const tr_element = tr[i];
            const preview_div = tr_element.querySelector('.search-preview');
            const contact_td = tr_element.children[0];
            const contact_link = contact_td.querySelector('a');
            const original_name = contact_td.getAttribute('data-original-name');

            if (contact_link) {{ contact_link.innerHTML = original_name; }}
            if (preview_div) {{ preview_div.innerHTML = ''; }}
            if (tr_element.hasAttribute('data-contact-search')) {{ tr_element.style.display = ""; }}
        }}
        return;
    }}


    for (let i = 0; i < tr.length; i++) {{ 
        const tr_element = tr[i];
        const preview_div = tr_element.querySelector('.search-preview');
        if (!preview_div) continue; 

        const contact_name = tr_element.getAttribute('data-contact-search');
        const last_contact_timestamp = parseFloat(tr_element.querySelector('[data-timestamp]').getAttribute('data-timestamp'));

        // 1. FILTRAGE PAR DATE 
        let is_date_match = true;
        if (tsStart !== null && last_contact_timestamp < tsStart) {{ is_date_match = false; }}
        if (tsEnd !== null && last_contact_timestamp >= tsEnd) {{ is_date_match = false; }}

        if (!is_date_match) {{
            tr_element.style.display = "none";
            continue;
        }}

        // 2. FILTRAGE PAR RECHERCHE TEXTUELLE
        let is_text_match = false;
        preview_div.innerHTML = ''; 

        // ... (Recherche dans le nom du contact inchangée)
        const contact_td = tr_element.children[0];
        const contact_link = contact_td.querySelector('a');
        const original_name = contact_td.getAttribute('data-original-name');
        contact_link.innerHTML = original_name; 

        if (filter.length > 0 && scopeName) {{ 
            let name_match = false;
            if (isFuzzyEnabled) {{
                 name_match = fuzzyMatch(contact_name, filter);
            }} else {{
                name_match = contact_name.indexOf(filter) > -1;
            }}
            
            if (name_match) {{ 
                is_text_match = true;

                const regex = new RegExp(filter, 'gi'); 
                const highlighted_name = original_name.replace(regex, (match) => '<strong>' + match + '</strong>');
                contact_link.innerHTML = highlighted_name;
            }}
        }}

        // 2.2 Recherche dans le contenu des messages
        const message_matches = []; 

        if (filter.length > 0 && scopeMessage && tr_element.messagesData) {{ 
            const SNIPPET_LENGTH = 50;
            const regex = new RegExp(filter, 'gi'); 

            for (const message of tr_element.messagesData) {{ 
                const message_text = message.text;
                
                let text_match = false;
                if (isFuzzyEnabled) {{
                    text_match = fuzzyMatch(message_text, filter);
                }} else {{
                    text_match = message_text.indexOf(filter) > -1;
                }}
                
                if (text_match) {{ 
                    is_text_match = true; 
                    
                    const match_index = message_text.indexOf(filter);
                    
                    let final_html;
                    
                    if (match_index > -1) {{
                        // Match exact
                        const start_index = Math.max(0, match_index - SNIPPET_LENGTH);
                        const end_index = Math.min(message_text.length, match_index + filter.length + SNIPPET_LENGTH);

                        let snippet = message_text.substring(start_index, end_index);
                        const highlighted_snippet = snippet.replace(regex, (match) => '<strong>' + match + '</strong>');
                        
                        let final_snippet = highlighted_snippet;
                        if (start_index > 0) final_snippet = '... ' + final_snippet;
                        if (end_index < message_text.length) final_snippet = final_snippet + ' ...';

                        final_html = '<span class="preview-date">' + message.date + '</span>' + final_snippet;
                        
                    }} else {{
                         // Match fuzzy (Traduction dynamique du label "Fuzzy")
                         final_html = '<span class="preview-date">' + message.date + texts.search_fuzzy + '</span>' + message_text.substring(0, 100) + '...';
                    }}
                    
                    message_matches.push({{ html: final_html, timestamp: message.ts }});
                }}
            }}

            // Trie les résultats du plus récent au plus ancien
            message_matches.sort((a, b) => b.timestamp - a.timestamp);

            if (message_matches.length > 0) {{ 
                const snippets_html = message_matches.map(m => m.html).join('<div class="snippet-separator"></div>');
                preview_div.innerHTML = snippets_html;
            }}
        }}
        
        // 3. Affichage/Masquage de la ligne
        if (tr_element.hasAttribute('data-contact-search')) {{ 
            const is_text_filter_active = filter.length > 0;
            
            const should_display = is_date_match && (!is_text_filter_active || is_text_match);
            
            if (should_display) {{ 
                tr_element.style.display = "";
            }} else {{ 
                tr_element.style.display = "none";
            }}
        }}
    }}
}}
</script>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

def main():
    ap = argparse.ArgumentParser(description="Génère un index HTML triable des contacts.")
    ap.add_argument("folder", help="Dossier contenant les fichiers .html (un par conversation).")
    ap.add_argument("-o", "--output", default="index.html", help="Chemin de sortie pour la page index (par défaut: index.html)")
    ap.add_argument("-l", "--lang", default="fr", choices=["fr", "en"], help="Langue de l'interface (fr ou en).")
    args = ap.parse_args()

    folder = args.folder
    if not os.path.isdir(folder):
        print(f"Erreur: {folder} n'est pas un dossier.")
        sys.exit(1)

    entries = []
    for name in os.listdir(folder):
        if not name.lower().endswith(".html"):
            continue
        path = os.path.join(folder, name)
        res = scan_file(path)
        if res:
            entries.append(res)

    if not entries:
        print("Aucune conversation exploitable trouvée (pas de timestamps reconnus).")
        sys.exit(2)

    build_index(entries, args.output, lang=args.lang)
    print(f"OK: index généré → {args.output} ({len(entries)} contacts). Vous pouvez changer la langue directement dans la page.")

if __name__ == "__main__":
    main()
