from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.utils import platform

import arabic_reshaper
from bidi.algorithm import get_display

FONT = "Vazirmatn-Regular.ttf"
SPEECH_REQUEST_CODE = 7314


def fa(text):
    try:
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def normalize_persian(text):
    return (str(text).replace("ي", "ی").replace("ك", "ک")
            .replace("\u200c", " ").strip())


def extract_name(command):
    command = normalize_persian(command).strip(" ؟?!.،؛")
    endings = ["زنگ بزن", "تماس بگیر", "تماس بزن"]
    for ending in endings:
        if command.endswith(ending):
            command = command[:-len(ending)].strip()
            break

    prefixes = ["لطفاً ", "لطفا ", "به ", "با ", "تماس با "]
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if command.startswith(prefix):
                command = command[len(prefix):].strip()
                changed = True

    for phrase in [" زنگ بزن", " تماس بگیر", " تماس بزن"]:
        command = command.replace(phrase, "").strip()
    return command.strip(" ؟?!.،؛")


class VoiceCallApp(App):
    def build(self):
        self.title = "برنامه تماس صوتی"
        self.found_number = None

        root = BoxLayout(orientation="vertical", padding=22, spacing=12)

        title = Label(text=fa("برنامه تماس صوتی"), font_name=FONT,
                      font_size=27, size_hint_y=0.75)

        self.command_input = TextInput(
            hint_text=fa("مثلاً: به علی زنگ بزن"),
            font_name=FONT, font_size=20, multiline=False,
            size_hint_y=1.15
        )

        self.speech_button = Button(text=fa("صحبت کنید"),
                                    font_name=FONT, font_size=20)
        self.check_button = Button(text=fa("بررسی دستور و جست‌وجوی مخاطب"),
                                   font_name=FONT, font_size=20)
        self.call_button = Button(text=fa("تماس با مخاطب پیدا‌شده"),
                                  font_name=FONT, font_size=20,
                                  disabled=True)

        self.result = Label(
            text=fa("دستور را تایپ کنید یا در اندروید از میکروفون استفاده کنید."),
            font_name=FONT, font_size=17, halign="center",
            valign="middle", size_hint_y=1.2
        )
        self.result.bind(size=lambda obj, value:
                         setattr(obj, "text_size", value))

        self.speech_button.bind(on_press=self.start_speech_recognition)
        self.check_button.bind(on_press=self.process_command)
        self.call_button.bind(on_press=self.dial_found_contact)

        root.add_widget(title)
        root.add_widget(self.command_input)
        root.add_widget(self.speech_button)
        root.add_widget(self.check_button)
        root.add_widget(self.call_button)
        root.add_widget(self.result)

        if platform == "android":
            try:
                from android import activity
                activity.bind(on_activity_result=self.on_activity_result)
            except Exception:
                pass
        return root

    def start_speech_recognition(self, instance):
        if platform != "android":
            self.result.text = fa(
                "میکروفون این نسخه فقط در اندروید آزمایش می‌شود. "
                "فعلاً دستور را در کادر بالا تایپ کنید."
            )
            return
        try:
            from jnius import autoclass
            from android.permissions import request_permissions, Permission

            def after_permission(permissions, grants):
                if not all(grants):
                    self.result.text = fa("برای استفاده از میکروفون، مجوز لازم است.")
                    return
                try:
                    PythonActivity = autoclass("org.kivy.android.PythonActivity")
                    Intent = autoclass("android.content.Intent")
                    RecognizerIntent = autoclass("android.speech.RecognizerIntent")
                    intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                                    RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "fa-AF")
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                                    "fa-AF")
                    intent.putExtra(RecognizerIntent.EXTRA_PROMPT,
                                    "دستور خود را بگویید")
                    PythonActivity.mActivity.startActivityForResult(
                        intent, SPEECH_REQUEST_CODE
                    )
                    self.result.text = fa("منتظر تشخیص صدای شما هستم...")
                except Exception as exc:
                    self.result.text = fa("تشخیص گفتار اجرا نشد: " + str(exc))

            request_permissions([Permission.RECORD_AUDIO], after_permission)
        except Exception as exc:
            self.result.text = fa("راه‌اندازی میکروفون ناموفق بود: " + str(exc))

    def on_activity_result(self, request_code, result_code, intent):
        if request_code != SPEECH_REQUEST_CODE:
            return
        try:
            from jnius import autoclass
            Activity = autoclass("android.app.Activity")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")
            if result_code != Activity.RESULT_OK or intent is None:
                self.result.text = fa("تشخیص صدا لغو شد یا نتیجه‌ای دریافت نشد.")
                return
            results = intent.getStringArrayListExtra(
                RecognizerIntent.EXTRA_RESULTS
            )
            if results is None or results.size() == 0:
                self.result.text = fa("متن گفتار دریافت نشد؛ دوباره تلاش کنید.")
                return
            self.command_input.text = str(results.get(0))
            self.result.text = fa("متن تشخیص داده‌شده:\n" + self.command_input.text)
        except Exception as exc:
            self.result.text = fa("خواندن نتیجه گفتار ناموفق بود: " + str(exc))

    def process_command(self, instance):
        command = self.command_input.text.strip()
        self.found_number = None
        self.call_button.disabled = True

        if not command:
            self.result.text = fa("لطفاً دستور را تایپ کنید یا بگویید.")
            return

        name = extract_name(command)
        if not name:
            self.result.text = fa("نام مخاطب از دستور تشخیص داده نشد.")
            return

        if platform != "android":
            self.result.text = fa(
                "نام استخراج‌شده از دستور: " + name +
                "\n\nجست‌وجوی مخاطبان واقعی فقط پس از اجرای APK روی گوشی اندروید انجام می‌شود."
            )
            return

        self.search_contact_on_android(name)

    def search_contact_on_android(self, name):
        try:
            from android.permissions import request_permissions, Permission

            def after_permission(permissions, grants):
                if not all(grants):
                    self.result.text = fa(
                        "برای جست‌وجوی مخاطبان، باید مجوز مخاطبان را اجازه بدهید."
                    )
                    return
                self._query_contacts(name)

            request_permissions([Permission.READ_CONTACTS], after_permission)
        except Exception as exc:
            self.result.text = fa("درخواست مجوز مخاطبان ناموفق بود: " + str(exc))

    def _query_contacts(self, name):
        cursor = None
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            ContactsContract = autoclass("android.provider.ContactsContract")
            Phone = ContactsContract.CommonDataKinds.Phone
            resolver = PythonActivity.mActivity.getContentResolver()
            uri = Phone.CONTENT_URI
            projection = ["display_name", "number"]
            cursor = resolver.query(uri, projection, None, None, "display_name ASC")

            wanted = normalize_persian(name).casefold()
            matches = []
            if cursor is not None:
                while cursor.moveToNext():
                    display_name = str(cursor.getString(0) or "")
                    number = str(cursor.getString(1) or "")
                    if wanted in normalize_persian(display_name).casefold():
                        matches.append((display_name, number))

            if not matches:
                self.found_number = None
                self.call_button.disabled = True
                self.result.text = fa(
                    "مخاطبی با نام «" + name + "» پیدا نشد.\n"
                    "املای نام را بررسی کنید یا نام دیگری را امتحان کنید."
                )
                return

            display_name, number = matches[0]
            self.found_number = number
            self.call_button.disabled = False
            if len(matches) > 1:
                extra = "\nچند مخاطب مشابه پیدا شد؛ فعلاً اولین مورد انتخاب شده است."
            else:
                extra = ""
            self.result.text = fa(
                "مخاطب پیدا شد:\n" + display_name +
                "\nشماره: " + number +
                extra +
                "\n\nبرای باز کردن صفحه تماس، دکمه پایین را بزنید."
            )
        except Exception as exc:
            self.result.text = fa("جست‌وجوی مخاطبان ناموفق بود: " + str(exc))
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def dial_found_contact(self, instance):
        if not self.found_number:
            self.result.text = fa("ابتدا یک مخاطب را پیدا کنید.")
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            intent = Intent(Intent.ACTION_DIAL)
            intent.setData(Uri.parse("tel:" + self.found_number))
            PythonActivity.mActivity.startActivity(intent)
        except Exception as exc:
            self.result.text = fa("باز کردن صفحه تماس ناموفق بود: " + str(exc))

    def on_stop(self):
        if platform == "android":
            try:
                from android import activity
                activity.unbind(on_activity_result=self.on_activity_result)
            except Exception:
                pass


if __name__ == "__main__":
    VoiceCallApp().run()
