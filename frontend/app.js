const API = "/api";
const storedLanguage = localStorage.getItem("homematch_lang");
const state = { type: "looking_for_room", token: localStorage.getItem("homematch_token"), user: null, lang: storedLanguage === "en" ? "en" : "tr", activePostId: null };
const words = {
  tr: { room:"Ev arıyorum", mate:"Ev arkadaşı arıyorum", city:"İl", district:"İlçe", budget:"Aylık kişi payı üst sınırı", search:"İlanları bul", title:"İyi bir ev, iyi bir ev arkadaşıyla başlar.", intro:"Kendine uygun evi ya da ev arkadaşını bul. Önce tanış, sonra birlikte karar ver.", signup:"Üye ol", login:"Giriş yap", logout:"Çıkış", create:"İlan oluştur", saved:"Kaydedilenler", inbox:"Mesajlar", mine:"İlanlarım", no:"Bu aramada henüz ilan yok.", loading:"İlanlar yükleniyor…", error:"Bir sorun oluştu.", type:"İlan türü", name:"Adın", email:"E-posta", password:"Parola (en az 10 karakter)", bio:"Kendini tanıt (en az 20 karakter)", posttitle:"İlan başlığı", desc:"İlan açıklaması", date:"Taşınma / müsaitlik tarihi", amount:"Aylık bütçen (₺)", share:"Kişi başı aylık kira (₺)", cityname:"İstanbul", districtname:"Kadıköy", submit:"Kaydet", cancel:"Vazgeç", detail:"İlan detayı", profile:"Tanıtım", needlogin:"Tanıtımı görmek için giriş yap.", message:"Mesaj gönder", match:"Uyumları bul", noresult:"Henüz uygun eşleşme yok.", utilities:"Faturalar hakkında", roomtype:"Oda tipi (ör. 2+1)", people:"Evde toplam kişi", photos:"Ev fotoğrafları (en fazla 5)", smoke:"Sigara kullanıyor musun?", pets:"Evcil hayvanın var mı?", smoking_allowed:"Evde sigaraya izin var mı?", pets_allowed:"Evcil hayvana izin var mı?", sleep:"Uyku düzeni", clean:"Temizlik beklentisi", guests:"Misafir sıklığı", early:"Erken", night:"Geç saatler", flexible:"Esnek", tidy:"Düzenli", average:"Ortalama", relaxed:"Rahat", rare:"Nadiren", sometimes:"Ara sıra", often:"Sık", yes:"Evet", no2:"Hayır", published:"İlanın yayınlandı.", matchscore:"uyum", send:"Gönder", message_placeholder:"Mesajını yaz…", none:"Henüz içerik yok.", peoplelabel:"Sana uygun kişiler", close:"Yayından kaldır", reopen:"Yeniden yayınla", all:"Aylık pay", roomsearch:"Ev arayanlar", matesearch:"Ev arkadaşı arayanlar", eyebrow:"Birlikte yaşamak daha kolay", headline:"İyi bir ev, iyi bir ev arkadaşıyla başlar.", subhead:"Kendine uygun evi ya da ev arkadaşını bul. Önce tanış, sonra birlikte karar ver.", tab_room:"Ev arıyorum", tab_roommate:"Ev arkadaşı arıyorum", max_budget:"Aylık kişi payı üst sınırı", latest:"Sana uygun kişiler", create_post:"İlan oluştur", footer:"Ev arkadaşı bulmanın daha iyi bir yolu.", detected:"İlan dili", translate:"Türkçeye çevir", translating:"Çevriliyor…", original:"Özgün metni göster", translated_by:"Makine çevirisi", translate_error:"Çeviri şu anda kullanılamıyor.", language_tr:"Türkçe", language_en:"İngilizce" },
  en: { room:"Looking for a home", mate:"Looking for a flatmate", city:"City", district:"District", budget:"Monthly share limit", search:"Find listings", title:"A good home starts with a good flatmate.", intro:"Find a home or a flatmate that fits you. Get to know each other, then decide together.", signup:"Join", login:"Log in", logout:"Log out", create:"Create listing", saved:"Saved", inbox:"Messages", mine:"My listings", no:"No listings match yet.", loading:"Loading listings…", error:"Something went wrong.", type:"Listing type", name:"Your name", email:"Email", password:"Password (at least 10 characters)", bio:"Introduce yourself (at least 20 characters)", posttitle:"Listing title", desc:"Listing description", date:"Move-in / available date", amount:"Your monthly budget (₺)", share:"Monthly share per person (₺)", cityname:"Istanbul", districtname:"Kadikoy", submit:"Save", cancel:"Cancel", detail:"Listing details", profile:"Introduction", needlogin:"Log in to view the introduction.", message:"Send a message", match:"Find matches", noresult:"No suitable matches yet.", utilities:"Bills information", roomtype:"Room type (e.g. 2+1)", people:"People in the home", photos:"Home photos (up to 5)", smoke:"Do you smoke?", pets:"Do you have pets?", smoking_allowed:"Is smoking allowed at home?", pets_allowed:"Are pets allowed?", sleep:"Sleep schedule", clean:"Cleanliness preference", guests:"Guest frequency", early:"Early", night:"Night owl", flexible:"Flexible", tidy:"Tidy", average:"Average", relaxed:"Relaxed", rare:"Rarely", sometimes:"Sometimes", often:"Often", yes:"Yes", no2:"No", published:"Your listing is live.", matchscore:"match", send:"Send", message_placeholder:"Write a message…", none:"Nothing here yet.", peoplelabel:"PEOPLE TO MATCH WITH", close:"Close listing", reopen:"Publish again", all:"Monthly share", roomsearch:"People looking for a home", matesearch:"People looking for a flatmate", eyebrow:"Sharing a home made easier", headline:"A good home starts with a good flatmate.", subhead:"Find a home or flatmate that fits you. Get to know each other, then decide together.", tab_room:"Looking for a home", tab_roommate:"Looking for a flatmate", max_budget:"Monthly share limit", latest:"People you may like", create_post:"Create listing", footer:"A better way to find a flatmate.", detected:"Listing language", translate:"Translate to English", translating:"Translating…", original:"Show original", translated_by:"Machine translated", translate_error:"Translation is unavailable right now.", language_tr:"Turkish", language_en:"English" }
};
const t = key => words[state.lang][key] || key;
function detectPostLanguage(text) {
  const value = String(text || "").toLocaleLowerCase();
  if (/[ışğüöç]/i.test(value) || /\b(ve|bir|için|ev|oda|arıyorum|kiralık|eşyalı|paylaşmak|uygun|merhaba|öğrenci|çalışan|bütçe|aylık|tercih|sigara|evcil|hayvan)\b/.test(value)) return "tr";
  return "en";
}
async function translateText(text, source, target) {
  let hash = 2166136261;
  for (const character of text) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  const cacheKey = "homematch_translation_" + source + "_" + target + "_" + (hash >>> 0).toString(36);
  try { const cached = localStorage.getItem(cacheKey); if (cached) return cached; } catch {}
  const sentences = String(text).match(/[^.!?\n]+[.!?]?\n*/g) || [String(text)];
  const chunks = [];
  let chunk = "";
  for (const sentence of sentences) {
    if (new TextEncoder().encode(chunk + sentence).length > 430 && chunk) { chunks.push(chunk); chunk = ""; }
    if (new TextEncoder().encode(sentence).length > 430) {
      let piece = "";
      for (const word of sentence.split(/(\s+)/)) {
        if (new TextEncoder().encode(piece + word).length > 430 && piece) { chunks.push(piece); piece = ""; }
        piece += word;
      }
      chunk += piece;
    } else chunk += sentence;
  }
  if (chunk) chunks.push(chunk);
  const translated = [];
  for (const part of chunks) {
    const data = await api("/translate", {
      method: "POST",
      body: JSON.stringify({ text: part, source_language: source, target_language: target }),
    });
    translated.push(data.translated_text);
  }
  const result = translated.join("");
  try { localStorage.setItem(cacheKey, result); } catch {}
  return result;
}
function applyLocale() {
  document.documentElement.lang = state.lang;
  document.querySelector("#language-toggle").textContent = state.lang === "tr" ? "EN" : "TR";
  document.querySelectorAll("[data-i18n]").forEach(node => { node.textContent = t(node.dataset.i18n); });
  document.querySelector("#city-filter").placeholder = t("cityname");
  document.querySelector("#district-filter").placeholder = t("districtname");
  document.querySelector("#budget-filter").placeholder = "₺";
  document.querySelectorAll(".choice-tab").forEach(tab => {
    const active = tab.dataset.type === state.type;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
  });
  document.querySelector("#results-title").textContent = state.type === "looking_for_room" ? t("roomsearch") : t("matesearch");
}
const escapeHtml = value => String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));
const dialog = document.querySelector("#dialog");
const body = document.querySelector("#dialog-content");
function html(id, value) { document.querySelector(id).innerHTML = value; }
function say(value, error) { const node = document.querySelector("#status"); node.textContent = value || ""; node.style.color = error ? "#b73d25" : ""; }
function api(path, options) {
  options = options || {};
  const headers = new Headers(options.headers || {});
  if (state.token) headers.set("Authorization", "Bearer " + state.token);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  return fetch(API + path, Object.assign({}, options, { headers: headers })).then(async response => {
    if (response.status === 204) return null;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || t("error"));
    return data;
  });
}
function open(title, content) {
  document.querySelector("#dialog-title").textContent = title;
  body.innerHTML = content;
  dialog.showModal();
}
function syncHeader() {
  ["login-button", "register-button"].forEach(id => { document.querySelector("#" + id).hidden = Boolean(state.user); });
  ["logout-button", "favorites-button", "inbox-button", "my-posts-button", "create-post-button"].forEach(id => { document.querySelector("#" + id).hidden = !state.user; });
  document.querySelector("#login-button").textContent = t("login");
  document.querySelector("#register-button").textContent = t("signup");
  document.querySelector("#logout-button").textContent = t("logout");
  document.querySelector("#favorites-button").textContent = t("saved");
  document.querySelector("#inbox-button").textContent = t("inbox");
  document.querySelector("#my-posts-button").textContent = t("mine");
  document.querySelector("#create-post-button").textContent = t("create");
}
function cards(posts, scored) {
  if (!posts.length) return '<div class="empty">' + escapeHtml(t("no")) + "</div>";
  return posts.map(item => {
    const post = item.post || item;
    const amount = post.monthly_share == null ? post.monthly_budget : post.monthly_share;
    const image = post.image_url || (post.images && post.images[0] && post.images[0].image_url) || (post.image_urls && post.image_urls[0]);
    const label = post.post_type === "looking_for_room" ? t("room") : t("mate");
    const breakdown = scored && item.breakdown ? '<p class="muted">' + (state.lang === "tr" ? "Konum" : "Location") + " " + item.breakdown.location + "% · " + (state.lang === "tr" ? "Kira" : "Rent") + " " + item.breakdown.rent + "% · " + (state.lang === "tr" ? "Yaşam tarzı" : "Lifestyle") + " " + item.breakdown.lifestyle + "% · " + (state.lang === "tr" ? "Tarih" : "Date") + " " + item.breakdown.move_date + "%</p>" : "";
    return '<article class="post-card" data-post="' + escapeHtml(post.id) + '"><div class="post-image">' + (image ? '<img src="' + escapeHtml(image) + '" alt="">' : "⌂") + '</div><div class="card-body"><span class="badge">' + escapeHtml(label) + '</span><h3>' + escapeHtml(post.title) + '</h3><div class="location">⌖ ' + escapeHtml(post.district) + ", " + escapeHtml(post.city) + '</div><div class="card-meta"><span>' + escapeHtml(post.available_from) + '</span><strong>' + (amount == null ? "—" : Number(amount).toLocaleString()) + ' ₺</strong></div>' + (scored ? '<div class="card-meta"><span>' + t("matchscore") + '</span><strong>' + item.score + '%</strong></div>' : "") + breakdown + '</div></article>';
  }).join("");
}
async function loadPosts() {
  say(t("loading"));
  const query = new URLSearchParams({ post_type: state.type });
  const city = document.querySelector("#city-filter").value.trim();
  const district = document.querySelector("#district-filter").value.trim();
  const budget = document.querySelector("#budget-filter").value;
  if (city) query.set("city", city);
  if (district) query.set("district", district);
  if (budget) query.set("max_monthly_share", budget);
  try {
    const posts = await api("/posts?" + query.toString());
    html("#post-grid", cards(posts, false));
    say("");
  } catch (error) { html("#post-grid", '<div class="empty">' + escapeHtml(error.message) + "</div>"); say(error.message, true); }
  document.querySelector("#results-title").textContent = state.type === "looking_for_room" ? t("roomsearch") : t("matesearch");
}
function authForm(register) {
  let form = '<form id="auth-form"><div class="form-grid">';
  if (register) form += field("display_name", t("name"), "text", true) + field("intro", t("bio"), "textarea", true);
  form += field("email", t("email"), "email", true) + field("password", t("password"), "password", true);
  form += '</div><div class="form-actions"><button class="button button-dark">' + t(register ? "signup" : "login") + "</button></div></form>";
  open(t(register ? "signup" : "login"), form);
  document.querySelector("#auth-form").addEventListener("submit", event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    api("/auth/" + (register ? "register" : "login"), { method:"POST", body:JSON.stringify(data) }).then(result => {
      state.token = result.access_token; state.user = result.user; localStorage.setItem("homematch_token", state.token);
      syncHeader(); dialog.close(); loadPosts();
    }).catch(error => alert(error.message));
  });
}
function field(name, label, type, required, value) {
  const content = type === "textarea" ? '<textarea name="' + name + '" ' + (required ? "required" : "") + (name === "intro" ? ' minlength="20" maxlength="1200"' : name === "description" ? ' minlength="30" maxlength="4000"' : "") + "></textarea>" : '<input name="' + name + '" type="' + type + '" ' + (required ? "required" : "") + (type === "password" && name === "password" ? ' minlength="10" maxlength="128"' : "") + (name === "available_from" ? ' min="' + new Date().toISOString().slice(0,10) + '"' : "") + (value ? ' value="' + escapeHtml(value) + '"' : "") + ">";
  return '<div class="field full"><label>' + escapeHtml(label) + "</label>" + content + "</div>";
}
function showDetail(id) {
  state.activePostId = id;
  api("/posts/" + id).then(async post => {
    const sourceLanguage = detectPostLanguage(post.title + " " + post.description);
    let profile = '<p class="muted">' + t("needlogin") + "</p>";
    if (state.user) {
      const result = await api("/posts/" + id + "/profile");
      profile = "<h3>" + escapeHtml(result.profile.display_name) + "</h3><p>" + escapeHtml(result.profile.intro) + "</p>";
      const lifestyle = result.post.seeker_lifestyle || result.post.household_rules;
      if (lifestyle) {
        const rows = [];
        const boolFields = result.post.seeker_lifestyle
          ? [["smokes", "smoke"], ["has_pets", "pets"]]
          : [["smoking_allowed", "smoking_allowed"], ["pets_allowed", "pets_allowed"]];
        boolFields.forEach(([key, label]) => rows.push([t(label), lifestyle[key] ? t("yes") : t("no2")]));
        [["sleep_schedule", { early:"early", night_owl:"night", flexible:"flexible" }],
          ["cleanliness", { tidy:"tidy", average:"average", relaxed:"relaxed" }],
          ["guest_frequency", { rare:"rare", sometimes:"sometimes", often:"often" }]].forEach(([key, values]) => {
          if (lifestyle[key]) rows.push([t(key === "sleep_schedule" ? "sleep" : key === "cleanliness" ? "clean" : "guests"), t(values[lifestyle[key]] || lifestyle[key])]);
        });
        profile += '<dl class="lifestyle-list">' + rows.map(([label, value]) => '<div><dt>' + escapeHtml(label) + '</dt><dd>' + escapeHtml(value) + '</dd></div>').join("") + "</dl>";
      }
    }
    let content = '<p class="muted">' + escapeHtml(post.district) + ", " + escapeHtml(post.city) + " · " + escapeHtml(post.available_from) + "</p>";
    if (post.image_urls && post.image_urls[0]) content += '<img class="detail-hero" src="' + escapeHtml(post.image_urls[0]) + '" alt="">';
    content += '<div class="listing-language"><span>' + t("detected") + ': ' + t(sourceLanguage === "tr" ? "language_tr" : "language_en") + '</span><button type="button" id="translate-listing" class="text-button">' + t("translate") + '</button><span id="translation-credit" class="muted" hidden>' + t("translated_by") + ' · MyMemory</span></div>';
    content += '<h2 id="detail-title-text" class="detail-title">' + escapeHtml(post.title) + '</h2><p id="detail-description-text" class="detail-copy">' + escapeHtml(post.description) + "</p><h3>" + t("profile") + "</h3>" + profile;
    content += '<div class="form-actions"><button id="detail-fav" class="button button-light">' + t("saved") + '</button><button id="detail-message" class="button button-dark">' + t("message") + "</button></div>";
    open(t("detail"), content);
    const translationButton = document.querySelector("#translate-listing");
    let translated = false;
    if (sourceLanguage === state.lang) translationButton.hidden = true;
    translationButton.onclick = async () => {
      if (translated) {
        translated = false;
        document.querySelector("#detail-title-text").textContent = post.title;
        document.querySelector("#detail-description-text").textContent = post.description;
        document.querySelector("#translation-credit").hidden = true;
        translationButton.textContent = t("translate");
        return;
      }
      translationButton.disabled = true;
      translationButton.textContent = t("translating");
      try {
        const [title, description] = await Promise.all([
          translateText(post.title, sourceLanguage, state.lang),
          translateText(post.description, sourceLanguage, state.lang),
        ]);
        document.querySelector("#detail-title-text").textContent = title;
        document.querySelector("#detail-description-text").textContent = description;
        document.querySelector("#translation-credit").hidden = false;
        translationButton.textContent = t("original");
        translated = true;
      } catch {
        translationButton.textContent = t("translate_error");
      } finally { translationButton.disabled = false; }
    };
    if (sourceLanguage !== state.lang) translationButton.click();
    document.querySelector("#detail-fav").onclick = () => {
      if (!state.user) return authForm(false);
      api("/me/favorites/" + id, { method:"PUT" }).catch(error => alert(error.message));
    };
    document.querySelector("#detail-message").onclick = () => {
      if (!state.user) return authForm(false);
      api("/posts/" + id + "/conversations", { method:"POST" }).then(conversation => showConversation(conversation.id, conversation.other_display_name, conversation.post_title)).catch(error => alert(error.message));
    };
  }).catch(error => alert(error.message));
}
function lifestyleFields(type) {
  function select(name, label, options) {
    return '<div class="field"><label>' + label + '</label><select name="' + name + '" required>' + options.map(x => '<option value="' + x[0] + '">' + x[1] + "</option>").join("") + "</select></div>";
  }
  const bool = (name, label) => select(name, label, [["false", t("no2")], ["true", t("yes")]]);
  const schedule = [["early",t("early")],["night_owl",t("night")],["flexible",t("flexible")]];
  const clean = [["tidy",t("tidy")],["average",t("average")],["relaxed",t("relaxed")]];
  const guests = [["rare",t("rare")],["sometimes",t("sometimes")],["often",t("often")]];
  if (type === "looking_for_room") return bool("smokes",t("smoke")) + bool("has_pets",t("pets")) + select("sleep_schedule",t("sleep"),schedule) + select("cleanliness",t("clean"),clean) + select("guest_frequency",t("guests"),guests);
  return bool("smoking_allowed",t("smoking_allowed")) + bool("pets_allowed",t("pets_allowed")) + select("sleep_schedule",t("sleep"),schedule) + select("cleanliness",t("clean"),clean) + select("guest_frequency",t("guests"),guests);
}
function createPost() {
  if (!state.user) return authForm(false);
  const typeOptions = '<option value="looking_for_room">' + t("room") + '</option><option value="looking_for_roommate">' + t("mate") + "</option>";
  const content = '<form id="post-form"><div class="form-grid"><div class="field full"><label>' + t("type") + '</label><select name="post_type" id="post-type">' + typeOptions + "</select></div>" +
    field("title",t("posttitle"),"text",true) + field("city",t("city"),"text",true) + field("district",t("district"),"text",true) +
    field("description",t("desc"),"textarea",true) + field("available_from",t("date"),"date",true) +
    '<div class="field" id="amount-field"><label>' + t("amount") + '</label><input name="amount" type="number" min="1" required></div>' +
    '<div class="field" id="room-field"><label>' + t("roomtype") + '</label><input name="room_type" maxlength="20"></div><div class="field" id="people-field"><label>' + t("people") + '</label><input name="total_roommates" type="number" min="1" max="20"></div>' +
    '<div class="field full" id="utilities-field"><label>' + t("utilities") + '</label><input name="utilities_note" maxlength="300"></div>' +
    '<div id="lifestyle" class="form-grid full"><div class="field full"><strong>' + t("profile") + "</strong></div>" + lifestyleFields(state.type) + "</div>" +
    '<div class="field full"><label>' + t("photos") + '</label><input name="photos" type="file" accept="image/jpeg,image/png,image/webp" multiple></div></div>' +
    '<div class="form-actions"><button type="button" id="cancel-post" class="button button-light">' + t("cancel") + '</button><button class="button button-dark">' + t("submit") + "</button></div></form>";
  open(t("create"), content);
  const select = document.querySelector("#post-type");
  select.value = state.type;
  function changeType() {
    state.type = select.value;
    const offering = state.type === "looking_for_roommate";
    document.querySelector("#amount-field label").textContent = t(offering ? "share" : "amount");
    ["room-field","people-field","utilities-field"].forEach(id => { document.querySelector("#" + id).hidden = !offering; });
    const old = document.querySelector("#lifestyle");
    const section = document.createElement("div"); section.id = "lifestyle"; section.className = "form-grid full"; section.innerHTML = lifestyleFields(state.type);
    old ? old.replaceWith(section) : document.querySelector('[name="photos"]').closest(".field").before(section);
  }
  select.onchange = changeType;
  document.querySelector("#cancel-post").onclick = () => dialog.close();
  document.querySelector("#post-form").onsubmit = async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const type = data.get("post_type");
    const payload = { post_type:type, title:data.get("title"), description:data.get("description"), city:data.get("city"), district:data.get("district"), available_from:data.get("available_from") };
    const bool = name => data.get(name) === "true";
    if (type === "looking_for_room") {
      payload.monthly_budget = Number(data.get("amount"));
      payload.seeker_lifestyle = { smokes:bool("smokes"), has_pets:bool("has_pets"), sleep_schedule:data.get("sleep_schedule"), cleanliness:data.get("cleanliness"), guest_frequency:data.get("guest_frequency") };
    } else {
      payload.monthly_share = Number(data.get("amount")); payload.room_type = data.get("room_type") || null;
      payload.total_roommates = data.get("total_roommates") ? Number(data.get("total_roommates")) : null;
      payload.utilities_note = data.get("utilities_note") || "";
      payload.household_rules = { smoking_allowed:bool("smoking_allowed"), pets_allowed:bool("pets_allowed"), sleep_schedule:data.get("sleep_schedule"), cleanliness:data.get("cleanliness"), guest_frequency:data.get("guest_frequency") };
    }
    const files = Array.from(form.querySelector('[name="photos"]').files);
    if (files.length > 5 || files.some(file => file.size > 10 * 1024 * 1024)) return alert(t("photos"));
    try {
      const post = await api("/posts", { method:"POST", body:JSON.stringify(payload) });
      for (const file of files) { const upload = new FormData(); upload.append("file",file); await api("/posts/" + post.id + "/images",{method:"POST",body:upload}); }
      dialog.close(); say(t("published")); await loadPosts();
    } catch (error) { alert(error.message); }
  };
}
async function showMine() {
  try {
    const posts = await api("/me/posts");
    open(t("mine"), posts.length ? posts.map(post => '<div class="post-card"><div class="card-body"><span class="badge">' + (post.is_active ? (state.lang === "tr" ? "Yayında" : "Active") : (state.lang === "tr" ? "Kapalı" : "Closed")) + '</span><h3>' + escapeHtml(post.title) + '</h3><button class="button button-light" data-match="' + escapeHtml(post.id) + '">' + t("match") + '</button> <button class="button button-light" data-toggle-post="' + escapeHtml(post.id) + '" data-active="' + post.is_active + '">' + t(post.is_active ? "close" : "reopen") + "</button></div></div>").join("") : '<div class="empty">' + t("none") + "</div>");
    document.querySelectorAll("[data-match]").forEach(button => button.onclick = () => api("/posts/" + button.dataset.match + "/matches").then(matches => open(t("match"), cards(matches,true) || t("noresult"))).catch(error => alert(error.message)));
    document.querySelectorAll("[data-toggle-post]").forEach(button => button.onclick = async () => {
      try { await api("/posts/" + button.dataset.togglePost, { method:"PATCH", body:JSON.stringify({ is_active:button.dataset.active !== "true" }) }); await showMine(); }
      catch (error) { alert(error.message); }
    });
  } catch (error) { alert(error.message); }
}
async function showFavorites() {
  try {
    const posts = await api("/me/favorites");
    open(t("saved"), posts.length ? posts.map(post => '<div>' + cards([post],false) + '<button class="button button-light" data-remove-favorite="' + escapeHtml(post.id) + '">' + (state.lang === "tr" ? "Kaldır" : "Remove") + "</button></div>").join("") : '<div class="empty">' + t("none") + "</div>");
    document.querySelectorAll("[data-remove-favorite]").forEach(button => button.onclick = async () => { await api("/me/favorites/" + button.dataset.removeFavorite,{method:"DELETE"}); await showFavorites(); });
  }
  catch (error) { alert(error.message); }
}
async function showConversation(id, name, title) {
  try {
    const messages = await api("/conversations/" + id + "/messages");
    const conversation = '<div class="message-list">' + messages.map(message => '<div class="message ' + (message.sender_id === state.user.id ? "mine" : "") + '">' + escapeHtml(message.body) + "</div>").join("") + '</div><form id="message-form" class="form-actions"><input class="field" name="body" maxlength="4000" placeholder="' + t("message_placeholder") + '" required><button class="button button-dark">' + t("send") + "</button></form>";
    open(name + " · " + title, conversation);
    document.querySelector("#message-form").onsubmit = async event => { event.preventDefault(); const text = new FormData(event.currentTarget).get("body"); await api("/conversations/" + id + "/messages",{method:"POST",body:JSON.stringify({body:text})}); showConversation(id,name,title); };
  } catch (error) { alert(error.message); }
}
async function showInbox() {
  try {
    const items = await api("/me/conversations");
    open(t("inbox"), items.length ? items.map(item => '<button class="conversation-row" data-convo="' + item.id + '" data-name="' + escapeHtml(item.other_display_name) + '" data-title="' + escapeHtml(item.post_title) + '"><strong>' + escapeHtml(item.other_display_name) + '</strong><span>' + escapeHtml(item.post_title) + "</span></button>").join("") : '<div class="empty">' + t("none") + "</div>");
    document.querySelectorAll("[data-convo]").forEach(button => button.onclick = () => showConversation(button.dataset.convo,button.dataset.name,button.dataset.title));
  } catch (error) { alert(error.message); }
}
document.querySelectorAll(".choice-tab").forEach(button => button.onclick = () => {
  state.type = button.dataset.type;
  applyLocale();
  loadPosts();
});
document.querySelector("#search-button").onclick = loadPosts;
document.querySelector("#create-post-button").onclick = createPost;
document.querySelector("#login-button").onclick = () => authForm(false);
document.querySelector("#register-button").onclick = () => authForm(true);
document.querySelector("#logout-button").onclick = () => { state.token=null; state.user=null; localStorage.removeItem("homematch_token"); syncHeader(); loadPosts(); };
document.querySelector("#my-posts-button").onclick = showMine;
document.querySelector("#favorites-button").onclick = showFavorites;
document.querySelector("#inbox-button").onclick = showInbox;
document.querySelector("#language-toggle").onclick = () => {
  state.lang = state.lang === "tr" ? "en" : "tr"; localStorage.setItem("homematch_lang",state.lang);
  applyLocale(); syncHeader(); loadPosts();
  if (state.activePostId && dialog.open) showDetail(state.activePostId);
};
document.querySelector("#dialog-close").onclick = () => dialog.close();
document.querySelector("#post-grid").onclick = event => { const card=event.target.closest("[data-post]"); if(card) showDetail(card.dataset.post); };
body.onclick = event => { if (event.target.closest("button")) return; const card=event.target.closest("[data-post]"); if(card) showDetail(card.dataset.post); };
async function init() {
  applyLocale();
  if(state.token) { try { state.user=await api("/auth/me"); } catch { state.token=null; localStorage.removeItem("homematch_token"); } }
  syncHeader(); await loadPosts();
}
init();
