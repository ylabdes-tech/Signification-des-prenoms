import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'  # Backend pour Windows 8
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.metrics import dp
import random
import json
import re
try:
    from jnius import autoclass
    from plyer import notification, share
except ImportError:
    autoclass = None
    notification = None
    share = None

# IDs AdMob de test
BANNER_AD_UNIT_ID = "ca-app-pub-3940256099942544/6300978111"
INTERSTITIAL_AD_UNIT_ID = "ca-app-pub-3940256099942544/1033173712"

class NameMeaningApp(BoxLayout):
    def __init__(self, **kwargs):
        super(NameMeaningApp, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(20)
        self.spacing = dp(10)
        
        # Configuration de la fenêtre
        Window.clearcolor = (0.95, 0.97, 1, 1)
        Window.size = (dp(360), dp(640))
        
        # Initialisation AdMob (seulement sur Android)
        self.admob_initialized = False
        self.interstitial = None
        if autoclass and os.name != 'nt':
            self.init_admob()
        
        # Base de données des prénoms (inchangée, mais extensible)
        self.name_meanings = {
            "Mohammed": {"signification": "Loué, digne de louanges", "origine": "Arabe", "genre": "Masculin", "description": "Le prénom du prophète de l'Islam, symbole de guidance et de sagesse."},
            "Fatima": {"signification": "Celle qui sèvre, abstinente", "origine": "Arabe", "genre": "Féminin", "description": "Prénom de la fille du prophète Mohammed, symbole de pureté et de dévotion."},
            # ... (autres prénoms inchangés)
            "Gabriel": {"signification": "Force de Dieu", "origine": "Hébraïque", "genre": "Masculin", "description": "Archange messager, symbole de communication divine."},
            "Gabrielle": {"signification": "Force de Dieu", "origine": "Hébraïque", "genre": "Féminin", "description": "Évoque la force et la communication divine."}
        }
        
        # Citations catégorisées (inchangées)
        self.quotes = {
            "Motivation": [
                "Votre force surpasse tous les obstacles.",
                # ... (autres citations inchangées)
            ],
            "Amour": [
                "Votre cœur rayonne d'une lumière infinie.",
                # ...
            ],
            "Sagesse": [
                "Votre sagesse guide ceux qui vous entourent.",
                # ...
            ]
        }
        self.all_quotes = [q for cat in self.quotes.values() for q in cat]
        
        # Système anti-répétition
        self.recent_quotes = []
        self.recent_quotes_limit = 10
        
        # Liste de prénoms
        self.random_names = list(self.name_meanings.keys())
        
        # Favoris
        self.favorites = self.load_favorites()
        
        # Mode sombre
        self.dark_mode = False
        
        # Mode actuel
        self.current_mode = "citation"
        
        self.setup_ui()
        Clock.schedule_interval(self.send_daily_quote, 86400)  # Notification quotidienne
    
    def init_admob(self):
        """Initialise AdMob pour Android"""
        try:
            MobileAds = autoclass('com.google.android.gms.ads.MobileAds')
            AdRequest = autoclass('com.google.android.gms.ads.AdRequest')
            AdView = autoclass('com.google.android.gms.ads.AdView')
            InterstitialAd = autoclass('com.google.android.gms.ads.interstitial.InterstitialAd')
            Activity = autoclass('org.kivy.android.PythonActivity')
            
            MobileAds.initialize(Activity.mActivity)
            self.admob_initialized = True
            
            # Bannière
            self.ad_view = AdView(Activity.mActivity)
            self.ad_view.setAdSize(autoclass('com.google.android.gms.ads.AdSize').BANNER)
            self.ad_view.setAdUnitId(BANNER_AD_UNIT_ID)
            ad_request = AdRequest.Builder().build()
            self.ad_view.loadAd(ad_request)
            
            # Interstitiel
            self.interstitial = InterstitialAd(Activity.mActivity)
            self.interstitial.setAdUnitId(INTERSTITIAL_AD_UNIT_ID)
            self.interstitial.loadAd(ad_request)
        except Exception as e:
            print(f"Erreur AdMob : {e}")
    
    def show_interstitial(self):
        """Affiche une publicité interstitielle"""
        if self.interstitial and self.interstitial.isLoaded():
            self.interstitial.show()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        with self.canvas.before:
            Color(0.1, 0.5, 0.8, 1)
            self.rect = Rectangle(size=Window.size, pos=self.pos)
        
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        self.title_label = Label(
            text="🌟 Citations & Significations 🌟",
            font_size=dp(20),
            bold=True,
            color=(0.1, 0.3, 0.6, 1),
            text_size=(None, None),
            halign="center",
            size_hint_y=None,
            height=dp(40)
        )
        self.add_widget(self.title_label)
        
        stats = Label(
            text="📜 Découvrez citations et significations de prénoms !",
            font_size=dp(12),
            color=(0.2, 0.6, 0.2, 1),
            size_hint_y=None,
            height=dp(25),
            markup=True
        )
        self.add_widget(stats)
        
        mode_container = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(45))
        
        self.citation_mode_btn = Button(
            text="💬 Citations",
            font_size=dp(14),
            background_color=(0.2, 0.6, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        self.citation_mode_btn.bind(on_press=self.set_citation_mode)
        mode_container.add_widget(self.citation_mode_btn)
        
        self.meaning_mode_btn = Button(
            text="📖 Significations",
            font_size=dp(14),
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1)
        )
        self.meaning_mode_btn.bind(on_press=self.set_meaning_mode)
        mode_container.add_widget(self.meaning_mode_btn)
        
        self.add_widget(mode_container)
        
        input_container = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(80))
        
        instruction = Label(
            text="Entrez un prénom :",
            font_size=dp(14),
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height=dp(25)
        )
        input_container.add_widget(instruction)
        
        self.input_field = TextInput(
            hint_text="Ex: Mohammed, Fatima, Rose...",
            multiline=False,
            size_hint=(1, None),
            height=dp(40),
            font_size=dp(16),
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            cursor_color=(0.2, 0.6, 0.8, 1),
            padding=[dp(10), dp(10)]
        )
        self.input_field.bind(on_text_validate=self.on_enter_pressed)
        self.input_field.bind(text=self.on_text_change)
        input_container.add_widget(self.input_field)
        
        self.add_widget(input_container)
        
        self.suggestions_label = Label(
            text="",
            font_size=dp(10),
            color=(0.5, 0.5, 0.8, 1),
            size_hint_y=None,
            height=dp(20),
            markup=True
        )
        self.add_widget(self.suggestions_label)
        
        buttons_container = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(45))
        
        self.submit_btn = Button(
            text="🔍 Obtenir",
            font_size=dp(16),
            bold=True,
            background_color=(0.2, 0.6, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        self.submit_btn.bind(on_press=self.get_result)
        buttons_container.add_widget(self.submit_btn)
        
        self.random_btn = Button(
            text="🎲 Aléatoire",
            font_size=dp(14),
            background_color=(0.6, 0.4, 0.8, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.4
        )
        self.random_btn.bind(on_press=self.get_random_name)
        buttons_container.add_widget(self.random_btn)
        
        self.share_btn = Button(
            text="📤 Partager",
            font_size=dp(14),
            background_color=(0.4, 0.7, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.4
        )
        self.share_btn.bind(on_press=self.share_content)
        buttons_container.add_widget(self.share_btn)
        
        self.add_widget(buttons_container)
        
        categories_container = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(35))
        
        self.category_dropdown = DropDown()
        categories = ["Toutes", "Motivation", "Amour", "Sagesse"]
        
        for cat in categories:
            btn = Button(text=cat, size_hint_y=None, height=dp(30))
            btn.bind(on_release=lambda btn: self.category_dropdown.select(btn.text))
            self.category_dropdown.add_widget(btn)
        
        self.category_btn = Button(
            text="📌 Toutes",
            font_size=dp(12),
            background_color=(0.7, 0.5, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.category_btn.bind(on_press=self.category_dropdown.open)
        self.category_dropdown.bind(on_select=lambda instance, x: setattr(self.category_btn, 'text', f"📌 {x}"))
        categories_container.add_widget(self.category_btn)
        
        self.theme_btn = Button(
            text="🌙 Mode sombre",
            font_size=dp(12),
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.5
        )
        self.theme_btn.bind(on_press=self.toggle_theme)
        categories_container.add_widget(self.theme_btn)
        
        favorites_btn = Button(
            text="⭐ Favoris",
            font_size=dp(12),
            background_color=(0.9, 0.4, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.5
        )
        favorites_btn.bind(on_press=self.show_favorites)
        categories_container.add_widget(favorites_btn)
        
        self.add_widget(categories_container)
        
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(6)
        )
        self.add_widget(self.progress_bar)
        
        scroll = ScrollView(size_hint=(1, 1))
        
        self.result_label = Label(
            text="🎯 Tapez un prénom pour découvrir une citation ou sa signification !",
            font_size=dp(14),
            color=(0.3, 0.3, 0.3, 1),
            text_size=(None, None),
            halign="center",
            valign="middle",
            markup=True
        )
        scroll.add_widget(self.result_label)
        
        self.add_widget(scroll)
        
        self.save_favorite_btn = Button(
            text="💾 Ajouter aux favoris",
            font_size=dp(12),
            background_color=(0.8, 0.3, 0.5, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(35)
        )
        self.save_favorite_btn.bind(on_press=self.save_favorite)
        self.add_widget(self.save_favorite_btn)
    
    def set_citation_mode(self, instance):
        self.current_mode = "citation"
        self.citation_mode_btn.background_color = (0.2, 0.6, 0.8, 1)
        self.meaning_mode_btn.background_color = (0.6, 0.6, 0.6, 1)
        self.submit_btn.text = "🔍 Obtenir une citation"
        self.category_btn.disabled = False
        self.category_btn.opacity = 1
        self.result_label.text = "🎯 Mode Citation activé ! Tapez un prénom pour une citation."
    
    def set_meaning_mode(self, instance):
        self.current_mode = "signification"
        self.meaning_mode_btn.background_color = (0.2, 0.6, 0.8, 1)
        self.citation_mode_btn.background_color = (0.6, 0.6, 0.6, 1)
        self.submit_btn.text = "🔍 Obtenir la signification"
        self.category_btn.disabled = True
        self.category_btn.opacity = 0.5
        self.result_label.text = "📖 Mode Signification activé ! Tapez un prénom pour sa signification."
    
    def get_name_meaning(self, name):
        """Recherche flexible avec tolérance aux fautes"""
        from difflib import get_close_matches
        name = name.strip().capitalize()
        
        # Recherche exacte
        if name in self.name_meanings:
            meaning = self.name_meanings[name]
            return {
                "found": True,
                "signification": meaning["signification"],
                "origine": meaning["origine"],
                "genre": meaning["genre"],
                "description": meaning["description"]
            }
        
        # Recherche approximative
        close_matches = get_close_matches(name, self.name_meanings.keys(), n=1, cutoff=0.8)
        if close_matches:
            meaning = self.name_meanings[close_matches[0]]
            return {
                "found": True,
                "signification": meaning["signification"],
                "origine": meaning["origine"],
                "genre": meaning["genre"],
                "description": meaning["description"]
            }
        
        return {
            "found": False,
            "message": "Signification non trouvée dans notre base de données"
        }
    
    def format_name_meaning(self, name):
        meaning_data = self.get_name_meaning(name)
        if meaning_data["found"]:
            result = f"[size=22][color=2d5aa0]✨ {name.capitalize()} ✨[/color][/size]\n\n"
            result += f"[size=14][color=7c2d12]📖 Signification :[/color] {meaning_data['signification']}[/size]\n"
            result += f"[size=14][color=7c2d12]🌍 Origine :[/color] {meaning_data['origine']}[/size]\n"
            result += f"[size=14][color=7c2d12]👤 Genre :[/color] {meaning_data['genre']}[/size]\n\n"
            result += f"[size=12][color=4a5568]💭 Description :[/color]\n{meaning_data['description']}[/size]"
            return result
        else:
            return f"❓ Désolé, la signification de '{name}' n'est pas encore dans notre base de données.\n\n💡 Essayez : {', '.join(random.sample(self.random_names, 3))}"
    
    def get_unique_quote(self, quotes_list):
        available_quotes = [q for q in quotes_list if q not in self.recent_quotes]
        if not available_quotes:
            self.recent_quotes = []
            available_quotes = quotes_list
        selected_quote = random.choice(available_quotes)
        self.recent_quotes.append(selected_quote)
        if len(self.recent_quotes) > self.recent_quotes_limit:
            self.recent_quotes.pop(0)
        return selected_quote
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def toggle_theme(self, instance):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            Window.clearcolor = (0.2, 0.2, 0.2, 1)
            self.rect.source = None
            with self.canvas.before:
                Color(0.1, 0.1, 0.3, 1)
                self.rect = Rectangle(size=Window.size, pos=self.pos)
            self.title_label.color = (0.8, 0.9, 1, 1)
            self.result_label.color = (0.9, 0.9, 0.9, 1)
            self.theme_btn.text = "☀️ Mode clair"
        else:
            Window.clearcolor = (0.95, 0.97, 1, 1)
            self.rect.source = None
            with self.canvas.before:
                Color(0.1, 0.5, 0.8, 1)
                self.rect = Rectangle(size=Window.size, pos=self.pos)
            self.title_label.color = (0.1, 0.3, 0.6, 1)
            self.result_label.color = (0.3, 0.3, 0.3, 1)
            self.theme_btn.text = "🌙 Mode sombre"
    
    def on_text_change(self, instance, value):
        if len(value) >= 2:
            from difflib import get_close_matches
            suggestions = get_close_matches(value, self.random_names, n=5, cutoff=0.6)
            if suggestions:
                self.suggestions_label.text = f"💡 Suggestions: {', '.join(suggestions)}"
            else:
                mode_text = "citation" if self.current_mode == "citation" else "signification"
                self.suggestions_label.text = f"🔍 Nouvelle {mode_text} à chaque recherche !"
        else:
            self.suggestions_label.text = ""
    
    def on_enter_pressed(self, instance):
        self.get_result(instance)
    
    def animate_progress(self):
        anim = Animation(value=100, duration=0.8)
        anim.bind(on_complete=lambda *args: setattr(self.progress_bar, 'value', 0))
        anim.start(self.progress_bar)
    
    def get_result(self, instance):
        name = self.input_field.text.strip()
        if not name:
            self.result_label.text = "⚠️ Veuillez entrer un prénom !"
            return
        
        self.animate_progress()
        if self.current_mode == "citation":
            self.get_quote_for_name(name)
        else:
            meaning_result = self.format_name_meaning(name)
            self.result_label.text = meaning_result
            self.result_label.text_size = (Window.width - dp(40), None)
        if self.admob_initialized and random.random() < 0.3:
            self.show_interstitial()
    
    def get_quote_for_name(self, name):
        category_text = self.category_btn.text.replace("📌 ", "")
        selected_quotes = self.quotes.get(category_text, self.all_quotes) if category_text != "Toutes" else self.all_quotes
        quote = self.get_unique_quote(selected_quotes)
        formatted_result = f"[size=20][color=2d5aa0]✨ {name.capitalize()} ✨[/color][/size]\n\n"
        formatted_result += f"[size=16][color=4a5568]💬 {quote}[/color][/size]\n\n"
        formatted_result += f"[size=12][color=7c2d12]🎯 Catégorie : {category_text}[/color][/size]"
        self.result_label.text = formatted_result
        self.result_label.text_size = (Window.width - dp(40), None)
    
    def get_random_name(self, instance):
        random_name = random.choice(self.random_names)
        self.input_field.text = random_name
        self.get_result(instance)
    
    def share_content(self, instance):
        if not hasattr(self, 'result_label') or not self.result_label.text:
            popup = Popup(
                title="Erreur",
                content=Label(text="Aucun contenu à partager !", font_size=dp(14)),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            return
        
        clean_text = re.sub(r'\[.*?\]', '', self.result_label.text)
        if share and os.name != 'nt':
            share.text(clean_text, app_name="Citations Positives")
        else:
            popup_content = BoxLayout(orientation='vertical', spacing=dp(10))
            popup_content.add_widget(Label(text="Contenu copié ! Vous pouvez le partager :", font_size=dp(14)))
            text_input = TextInput(
                text=clean_text,
                multiline=True,
                readonly=True,
                font_size=dp(12),
                size_hint_y=0.7
            )
            popup_content.add_widget(text_input)
            close_btn = Button(text="Fermer", size_hint_y=None, height=dp(40))
            popup_content.add_widget(close_btn)
            popup = Popup(
                title="Partager",
                content=popup_content,
                size_hint=(0.9, 0.7)
            )
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
    
    def send_daily_quote(self, dt):
        """Envoie une notification quotidienne"""
        if notification and os.path.exists("icon.ico"):
            quote = random.choice(self.all_quotes)
            notification.notify(
                title="Citation du jour",
                message=quote,
                app_name="Citations Positives",
                app_icon="icon.ico"
            )
    
    def save_favorite(self, instance):
        if not hasattr(self, 'result_label') or not self.result_label.text or not self.input_field.text:
            popup = Popup(
                title="Erreur",
                content=Label(text="Aucun contenu à sauvegarder !", font_size=dp(14)),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            return
        
        name = self.input_field.text.strip().capitalize()
        content = self.result_label.text
        if name not in [fav['name'] for fav in self.favorites]:
            favorite_item = {
                'name': name,
                'content': content,
                'mode': self.current_mode,
                'timestamp': Clock.get_time()
            }
            self.favorites.append(favorite_item)
            self.save_favorites_to_file()
            self.save_favorite_btn.text = "✅ Ajouté !"
            Clock.schedule_once(lambda dt: setattr(self.save_favorite_btn, 'text', "💾 Ajouter aux favoris"), 2)
        else:
            self.save_favorite_btn.text = "📌 Déjà en favoris"
            Clock.schedule_once(lambda dt: setattr(self.save_favorite_btn, 'text', "💾 Ajouter aux favoris"), 2)
    
    def show_favorites(self, instance):
        if not self.favorites:
            popup = Popup(
                title="Favoris",
                content=Label(text="Aucun favori sauvegardé pour le moment !", font_size=dp(14)),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            return
        
        popup_content = BoxLayout(orientation='vertical', spacing=dp(5))
        scroll = ScrollView()
        favorites_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        favorites_layout.bind(minimum_height=favorites_layout.setter('height'))
        
        for fav in reversed(self.favorites[-20:]):
            fav_container = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(80))
            fav_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
            name_label = Label(
                text=f"✨ {fav['name']} ({fav['mode']})",
                font_size=dp(12),
                color=(0.2, 0.4, 0.8, 1),
                size_hint_x=0.7
            )
            fav_header.add_widget(name_label)
            load_btn = Button(
                text="📋 Charger",
                size_hint_x=0.3,
                size_hint_y=None,
                height=dp(25),
                font_size=dp(10)
            )
            load_btn.bind(on_press=lambda x, fav=fav: self.load_favorite(fav))
            fav_header.add_widget(load_btn)
            fav_container.add_widget(fav_header)
            clean_preview = re.sub(r'\[.*?\]', '', fav['content'])
            preview_text = clean_preview.split('\n')[0][:50] + "..." if len(clean_preview) > 50 else clean_preview.split('\n')[0]
            preview_label = Label(
                text=preview_text,
                font_size=dp(10),
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(20)
            )
            fav_container.add_widget(preview_label)
            favorites_layout.add_widget(fav_container)
        
        scroll.add_widget(favorites_layout)
        popup_content.add_widget(scroll)
        clear_btn = Button(text="🗑️ Effacer tous les favoris", size_hint_y=None, height=dp(40))
        clear_btn.bind(on_press=lambda x: self.clear_favorites())
        popup_content.add_widget(clear_btn)
        close_btn = Button(text="Fermer", size_hint_y=None, height=dp(40))
        popup_content.add_widget(close_btn)
        popup = Popup(
            title=f"⭐ Mes Favoris ({len(self.favorites)})",
            content=popup_content,
            size_hint=(0.95, 0.8)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def load_favorite(self, favorite):
        self.input_field.text = favorite['name']
        self.result_label.text = favorite['content']
        self.result_label.text_size = (Window.width - dp(40), None)
        if favorite['mode'] == "citation":
            self.set_citation_mode(None)
        else:
            self.set_meaning_mode(None)
    
    def clear_favorites(self):
        self.favorites = []
        self.save_favorites_to_file()
    
    def load_favorites(self):
        try:
            if os.path.exists("favorites.json"):
                with open("favorites.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur chargement favoris : {e}")
        return []
    
    def save_favorites_to_file(self):
        try:
            with open("favorites.json", "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde favoris : {e}")

class NameMeaningMainApp(App):
    def build(self):
        return NameMeaningApp()

    def on_start(self):
        Clock.schedule_once(self.show_welcome, 0.5)
    
    def show_welcome(self, dt):
        welcome_content = BoxLayout(orientation='vertical', spacing=dp(15))
        welcome_text = Label(
            text="🌟 Bienvenue dans Citations & Significations ! 🌟\n\n"
                 "✨ Découvrez des citations inspirantes\n"
                 "📖 Explorez les significations de prénoms\n"
                 "⭐ Sauvegardez vos favoris\n\n"
                 "Commencez en tapant un prénom !",
            font_size=dp(14),
            halign="center",
            markup=True
        )
        welcome_content.add_widget(welcome_text)
        ok_btn = Button(
            text="🚀 Commencer !",
            size_hint_y=None,
            height=dp(45),
            font_size=dp(16)
        )
        welcome_content.add_widget(ok_btn)
        popup = Popup(
            title="Bienvenue !",
            content=welcome_content,
            size_hint=(0.85, 0.6),
            auto_dismiss=False
        )
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == "__main__":
    NameMeaningMainApp().run()