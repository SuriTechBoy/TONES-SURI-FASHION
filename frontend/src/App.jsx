import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "";
const SUGGESTED_QUESTIONS = [
  "Show me black t-shirts",
  "Show me oversized t-shirts under ₹1000",
  "What is your return policy?",
  "How can I track my order?",
  "Can I pay using COD?",
];

const FEATURE_ITEMS = [
  { icon: "✦", title: "AI Shopping Assistant", text: "Ask naturally about products, sizes, prices, shipping, returns and more." },
  { icon: "⌁", title: "Smart Product Search", text: "Find products using colour, fit, category and budget-style requests." },
  { icon: "◈", title: "Verified Knowledge", text: "Answers are grounded in the current TONES Fashion knowledge base." },
  { icon: "↗", title: "Product Discovery", text: "Open matching products directly from the assistant." },
];

const FLOATING_GARMENTS = [
  { image: "https://www.tonesfashion.com/cdn/shop/files/Main_4de729d4-17e8-4212-93cd-8056fe0694cb.jpg?v=1788264430", label: "THE ALPHA · TEE", className: "garment-one" },
  { image: "https://www.tonesfashion.com/cdn/shop/files/Yellow_Main.jpg?v=1788264183", label: "THE FINAL ACT · TEE", className: "garment-two" },
  { image: "https://www.tonesfashion.com/cdn/shop/files/Main_7.jpg?v=1789996422", label: "BLUE OXFORD · SHIRT", className: "garment-three" },
  { image: "https://www.tonesfashion.com/cdn/shop/files/Green_Main_jpg.jpg?v=1790059169", label: "SAGE OXFORD · SHIRT", className: "garment-four" },
];


function GarmentSvg({ type }) {
  if (type === "hoodie") {
    return (
      <svg viewBox="0 0 220 260" className="garment-svg" aria-hidden="true">
        <defs>
          <linearGradient id="hoodieGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#ec4899" />
          </linearGradient>
        </defs>
        <path d="M76 42c8-20 60-20 68 0l30 25 30 80-31 13-14-42v91H61v-91l-14 42-31-13 30-80z" fill="url(#hoodieGradient)" />
        <path d="M77 43c8 30 58 30 66 0" fill="none" stroke="rgba(255,255,255,.65)" strokeWidth="6" />
        <path d="M72 174h76v31H72z" fill="rgba(255,255,255,.16)" />
        <path d="M92 62c10 8 26 8 36 0" fill="none" stroke="rgba(255,255,255,.7)" strokeWidth="3" />
      </svg>
    );
  }
  if (type === "shirt") {
    return (
      <svg viewBox="0 0 220 260" className="garment-svg" aria-hidden="true">
        <defs>
          <linearGradient id="shirtGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="100%" stopColor="#2563eb" />
          </linearGradient>
        </defs>
        <path d="M72 48l36-18h4c7 12 19 12 26 0h4l36 18 27 34-30 24-12-18v91H57V88L45 106 15 82z" fill="url(#shirtGradient)" />
        <path d="M103 32c4 15 10 22 17 22s13-7 17-22" fill="none" stroke="rgba(255,255,255,.75)" strokeWidth="5" />
        <path d="M75 125h70" stroke="rgba(255,255,255,.22)" strokeWidth="4" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 220 260" className="garment-svg" aria-hidden="true">
      <defs>
        <linearGradient id="teeGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f97316" />
          <stop offset="50%" stopColor="#f43f5e" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
      </defs>
      <path d="M71 42l37-17h4l37 17 46 36-29 35-17-16v80H71V97L54 113 25 78z" fill="url(#teeGradient)" />
      <path d="M98 27c4 17 20 17 24 0" fill="none" stroke="rgba(255,255,255,.75)" strokeWidth="5" />
      <path d="M78 126h64" stroke="rgba(255,255,255,.22)" strokeWidth="4" />
      <circle cx="110" cy="158" r="14" fill="rgba(255,255,255,.18)" />
    </svg>
  );
}
const NEW_DROPS = [
  { name: "Yellow Oxford Shirt", price: "₹1,499", image: "https://www.tonesfashion.com/cdn/shop/files/Main_11.jpg?v=1789996923", tag: "NEW DROP" },
  { name: "Sage Oxford Shirt", price: "₹1,499", image: "https://www.tonesfashion.com/cdn/shop/files/Green_Main_jpg.jpg?v=1790059169", tag: "NEW DROP" },
  { name: "Pink Oxford Shirt", price: "₹1,499", image: "https://www.tonesfashion.com/cdn/shop/files/Main_10.jpg?v=1789996819", tag: "NEW DROP" },
  { name: "Light Blue Satin Shirt", price: "₹1,499", image: "https://www.tonesfashion.com/cdn/shop/files/light_blue_main_photo.jpg?v=1786970880", tag: "40% OFF" },
  { name: "Burgundy Satin Shirt", price: "₹1,499", image: "https://www.tonesfashion.com/cdn/shop/files/Main_1_999a28e0-7b3b-412d-a8f9-4131740fac7b.jpg?v=1786628488", tag: "NEW DROP" },
  { name: "Navy Blue Satin Shirt", price: "₹1,499", image: "https://www.tonesfashion.com/cdn/shop/files/Main_3_20c4fe30-6b20-42ae-a0fa-b896b7e29557.jpg?v=1786628708", tag: "NEW DROP" },
];

const CATEGORY_ITEMS = [
  { title: "T-SHIRTS", subtitle: "Everyday essentials", image: "https://www.tonesfashion.com/cdn/shop/files/Main_4de729d4-17e8-4212-93cd-8056fe0694cb.jpg?v=1788264430" },
  { title: "SHORT KURTAS", subtitle: "Modern Indian style", image: "https://www.tonesfashion.com/cdn/shop/files/Main_11.jpg?v=1789996923" },
  { title: "SHIRTS", subtitle: "Sharp, relaxed, effortless", image: "https://www.tonesfashion.com/cdn/shop/files/Main_7.jpg?v=1789996422" },
  { title: "SWEATSHIRTS", subtitle: "Easy layers", image: "https://www.tonesfashion.com/cdn/shop/files/Yellow_Main.jpg?v=1788264183" },
  { title: "BOTTOM WEAR", subtitle: "Cargos, chinos & more", image: "https://www.tonesfashion.com/cdn/shop/files/Main_v1_jpg.jpg?v=1786970476" },
];

const STANDARD_ITEMS = [
  ["01", "Fine fabric, sourced with care", "We choose the fabric before we choose the print."],
  ["02", "Made with real love and attention", "Small-batch runs, not rushed off a line."],
  ["03", "Designed to be comfortable", "Looks good, wears better."],
  ["04", "Cut to fit your style, not just your size", "Regular, relaxed, oversized."],
  ["05", "Built keeping the Indian man in mind", "Our climate, our bodies, our everyday."],
  ["06", "Checked by hand before it ships", "Every piece inspected, not just sampled."],
  ["07", "Made to outlast the season", "Built to stay in rotation, year after year."],
];

const COMMUNITY_IMAGES = [
  "https://www.tonesfashion.com/cdn/shop/files/Main_4de729d4-17e8-4212-93cd-8056fe0694cb.jpg?v=1788264430",
  "https://www.tonesfashion.com/cdn/shop/files/Main_7.jpg?v=1789996422",
  "https://www.tonesfashion.com/cdn/shop/files/Green_Main_jpg.jpg?v=1790059169",
  "https://www.tonesfashion.com/cdn/shop/files/Yellow_Main.jpg?v=1788264183",
  "https://www.tonesfashion.com/cdn/shop/files/Main_10.jpg?v=1789996819",
];

function Home({ onOpenAssistant }) {
  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <div className="home-page">
      <div className="home-noise" />

      {/* HERO — keep the existing Wear your vibe / Ask the AI experience */}
      <section className="hero-section">
        <video className="hero-background-video" autoPlay muted loop playsInline preload="auto" aria-hidden="true">
          <source src="/videos/tones-home-demo.mp4" type="video/mp4" />
        </video>
        <div className="hero-video-overlay" />

        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-dot" />TONES FASHION · AI SHOPPING</div>
          <h1>Wear your vibe.<br /><span>Ask the AI.</span></h1>
          <p className="hero-description">Discover TONES Fashion through a smarter shopping experience. Ask for a style, colour, fit or budget — and let the assistant find it.</p>
          <div className="hero-actions">
            <button className="primary-cta" onClick={onOpenAssistant}>Open AI Assistant <span>↗</span></button>
            <button className="ghost-cta" onClick={() => scrollTo("new-drops")}>Explore the collection ↓</button>
          </div>
          <div className="hero-proof">
            <div className="proof-item"><strong>AI</strong><span>RAG powered</span></div><div className="proof-line" />
            <div className="proof-item"><strong>24/7</strong><span>Always ready</span></div><div className="proof-line" />
            <div className="proof-item"><strong>∞</strong><span>Natural queries</span></div>
          </div>
        </div>

        <div className="fashion-stage" aria-label="TONES Fashion product showcase">
          <div className="stage-glow glow-a" /><div className="stage-glow glow-b" />
          <div className="orbit orbit-a" /><div className="orbit orbit-b" />
          <div className="stage-core"><div className="core-ring" /><div className="core-label">TONES<br /><span>AI</span></div></div>
          {FLOATING_GARMENTS.map((garment) => (
            <div className={`floating-garment ${garment.className}`} key={garment.className}>
              <div className="garment-card"><img src={garment.image} alt={garment.label} className="real-garment-image" loading="eager" /><span>{garment.label}</span></div>
            </div>
          ))}
          <div className="floating-chip chip-one">BLACK · OVERSIZED</div>
          <div className="floating-chip chip-two">UNDER ₹1000</div>
          <div className="floating-chip chip-three">SMART SEARCH ✦</div>
        </div>
      </section>

      <div className="marquee-wrap" aria-hidden="true"><div className="marquee-track">{Array.from({ length: 2 }).flatMap((_, row) => ["NEW DROP", "AI SHOPPING", "TONES FASHION", "FIND YOUR FIT", "STYLE · SEARCH · DISCOVER"].map((t, i) => <span key={`${row}-${i}`}>{t} <b>✦</b></span>))}</div></div>

      {/* NEW DROP */}
      <section className="shop-section" id="new-drops">
        <div className="shop-section-heading">
          <div><div className="eyebrow">FRESH FROM TONES</div><h2>New <span>Drop.</span></h2><p>Latest pieces from the current TONES Fashion collection.</p></div>
          <button className="section-link" onClick={onOpenAssistant}>Shop with AI ↗</button>
        </div>
        <div className="product-showcase-grid">
          {NEW_DROPS.map((item) => <article className="showcase-card" key={item.name}>
            <div className="showcase-image"><img src={item.image} alt={item.name} loading="lazy" /><span>{item.tag}</span></div>
            <div className="showcase-meta"><h3>{item.name}</h3><strong>{item.price}</strong></div>
          </article>)}
        </div>
      </section>

      {/* CATEGORIES */}
      <section className="categories-section" id="categories">
        <div className="shop-section-heading centered-heading"><div><div className="eyebrow">SHOP BY CATEGORY</div><h2>Find your <span>lane.</span></h2></div></div>
        <div className="category-grid">
          {CATEGORY_ITEMS.map((item) => <button className="category-card" key={item.title} onClick={onOpenAssistant}>
            <img src={item.image} alt={item.title} loading="lazy" /><div className="category-gradient" /><div className="category-copy"><small>{item.subtitle}</small><strong>{item.title}</strong><span>Explore ↗</span></div>
          </button>)}
        </div>
      </section>

      {/* COMMUNITY */}
      <section className="community-section">
        <div className="community-header"><div><div className="eyebrow">TONESCLAN</div><h2>Real people.<br /><span>Real fits.</span></h2></div><div><p>Wear it your way. Tag <strong>@tones_fashion</strong> to get featured.</p><button className="dark-pill" onClick={() => scrollTo("footer")}>Join the community ↗</button></div></div>
        <div className="community-strip">{COMMUNITY_IMAGES.map((image, i) => <div className="community-tile" key={`${image}-${i}`}><img src={image} alt="TONES Fashion community style" loading="lazy" /></div>)}</div>
      </section>

      {/* SHORT KURTAS / CASUALS */}
      <section className="editorial-section">
        <div className="editorial-heading"><div><div className="eyebrow">CURATED FOR YOU</div><h2>Short Kurtas<br /><span>& Casuals.</span></h2></div><button className="section-link" onClick={onOpenAssistant}>Find my fit ↗</button></div>
        <div className="editorial-grid">
          <article className="editorial-card"><img src="https://www.tonesfashion.com/cdn/shop/files/Main_10.jpg?v=1789996819" alt="Short Kurta style" loading="lazy" /><div><small>SHORT KURTAS</small><strong>Modern Indian, made easy.</strong><button onClick={onOpenAssistant}>Shop the edit ↗</button></div></article>
          <article className="editorial-card"><img src="https://www.tonesfashion.com/cdn/shop/files/light_blue_main_photo.jpg?v=1786970880" alt="Casual shirt style" loading="lazy" /><div><small>CASUALS</small><strong>Relaxed pieces for everyday.</strong><button onClick={onOpenAssistant}>Shop the edit ↗</button></div></article>
        </div>
      </section>

      {/* CARGOS / ESSENTIALS */}
      <section className="essentials-section">
        <div className="essentials-panel"><div><div className="eyebrow">ESSENTIALS</div><h2>Cargos<br /><span>In Town.</span></h2><p>Easy utility, everyday comfort and a fit that stays in rotation.</p><button className="primary-cta" onClick={onOpenAssistant}>Ask AI for cargos ↗</button></div><div className="essential-image"><img src="https://www.tonesfashion.com/cdn/shop/files/Main_v1_jpg.jpg?v=1786970476" alt="TONES Fashion essential" loading="lazy" /></div></div>
      </section>

      {/* TONES STANDARD */}
      <section className="standard-section" id="standard">
        <div className="standard-heading"><div className="eyebrow">THE TONES STANDARD</div><h2>What goes into<br /><span>every TONES piece.</span></h2><p>Seven things we never compromise on. Made for Indian men.</p></div>
        <div className="standard-list">{STANDARD_ITEMS.map(([number, title, text]) => <article className="standard-item" key={number}><span>{number}</span><div><h3>{title}</h3><p>{text}</p></div></article>)}</div>
      </section>

      {/* WHY TONES AI — preserved feature */}
      <section className="feature-section" id="features">
        <div className="section-heading"><div className="eyebrow">WHY TONES AI</div><h2>More than a chatbot.<br /><span>A shopping companion.</span></h2><p>The customer experience connects to the existing FastAPI + RAG + Mock LLM stack.</p></div>
        <div className="feature-grid">{FEATURE_ITEMS.map((item, index) => <article className="feature-card" key={item.title}><div className="feature-number">0{index + 1}</div><div className="feature-icon">{item.icon}</div><h3>{item.title}</h3><p>{item.text}</p><div className="feature-arrow">↗</div></article>)}</div>
      </section>

      {/* TRY IT */}
      <section className="discover-section" id="try-it"><div className="discover-panel"><div><div className="eyebrow">TRY IT YOUR WAY</div><h2>From “black tee”<br />to <span>“find my fit.”</span></h2><p>Natural language is the interface. No filters to fight with. Just ask.</p></div><div className="query-cloud">{["Black oversized tee", "Under ₹800", "What sizes?", "Return policy", "COD?", "Track my order"].map((q, i) => <button key={q} style={{ "--i": i }} onClick={onOpenAssistant}>{q}</button>)}</div></div></section>

      {/* FOOTER */}
      <footer className="home-footer" id="footer">
        <div className="footer-brand"><strong>TONES</strong><span>FASHION AI</span><p>AI-powered shopping experience for TONES Fashion.</p></div>
        <div className="footer-column"><h4>Explore</h4><button onClick={() => scrollTo("new-drops")}>New Drop</button><button onClick={() => scrollTo("categories")}>Categories</button><button onClick={() => scrollTo("standard")}>TONES Standard</button><button onClick={onOpenAssistant}>AI Assistant</button></div>
        <div className="footer-column"><h4>TONES</h4><span>About Us</span><span>Contact</span><span>Returns & Exchange</span><span>Shipping</span></div>
        <div className="footer-column"><h4>Built by STIF.AI</h4><p>AI product engineering, knowledge systems and intelligent customer experiences.</p><div className="social-links"><a href="https://www.linkedin.com/" target="_blank" rel="noreferrer">LinkedIn</a><a href="https://www.instagram.com/" target="_blank" rel="noreferrer">Instagram</a><a href="https://github.com/" target="_blank" rel="noreferrer">GitHub</a></div></div>
        <div className="footer-bottom"><span>© 2026 TONES Fashion AI · Built with STIF.AI</span><span>RAG · Knowledge · Conversation</span></div>
      </footer>
    </div>
  );
}

function ProductCard({ product }) {
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <div className="product-card">
      <div className="product-image-placeholder">
        {product.image_url && !imageFailed ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="product-image"
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="product-image-fallback">
            <GarmentSvg type="tee" />
          </div>
        )}

        <span className="product-image-badge">TONES</span>
      </div>

      <div className="product-card-content">
        <div className="product-title">{product.name}</div>

        {product.price !== null && product.price !== undefined && (
          <div className="product-price">
            ₹{Number(product.price).toLocaleString("en-IN")}
          </div>
        )}

        <div className="product-details">
          {product.color && (
            <div>
              <span className="detail-label">Color:</span> {product.color}
            </div>
          )}

          {product.fit && (
            <div>
              <span className="detail-label">Fit:</span> {product.fit}
            </div>
          )}

          {product.fabric && (
            <div>
              <span className="detail-label">Fabric:</span> {product.fabric}
            </div>
          )}
        </div>

        {product.listed_sizes?.length > 0 && (
          <div className="size-section">
            <div className="size-title">Listed sizes</div>

            <div className="size-list">
              {product.listed_sizes.map((size) => (
                <span key={size} className="size-pill">
                  {size}
                </span>
              ))}
            </div>
          </div>
        )}

        {product.currently_in_stock_sizes?.length > 0 && (
          <div className="stock-section">
            <div className="stock-title">
              Recorded in-stock sizes
            </div>

            <div className="stock-list">
              {product.currently_in_stock_sizes.map((size) => (
                <span key={size} className="stock-pill">
                  {size}
                </span>
              ))}
            </div>

            <div className="stock-note">
              Based on the current knowledge snapshot.
              This is not live inventory.
            </div>
          </div>
        )}

        <a
          href={product.url}
          target="_blank"
          rel="noreferrer"
          className="view-product-button"
        >
          View Product ↗
        </a>
      </div>
    </div>
  );
}

function ReviewCard({ review }) {
  return (
    <article className="review-card">
      <div className="review-card-top">
        <div className="review-avatar">{(review.author || "A").slice(0, 1).toUpperCase()}</div>
        <div>
          <strong>{review.author || "Anonymous"}</strong>
          <div className="review-meta">{"★".repeat(Number(review.rating || 0))}{"☆".repeat(Math.max(0, 5 - Number(review.rating || 0)))} {review.rating ?? "-"}/5</div>
        </div>
        {review.verified_buyer && <span className="verified-badge">Verified buyer</span>}
      </div>
      <p>{review.body}</p>
      {review.date && <small>{String(review.date).replace(" UTC", "")}</small>}
    </article>
  );
}

function Assistant({ onHome }) {
  const [sessionId, setSessionId] = useState(() => {
    try { return crypto.randomUUID(); } catch { return `tones-${Date.now()}-${Math.random().toString(36).slice(2)}`; }
  });
  const [messages, setMessages] = useState([{ id: 1, role: "assistant", content: "Hi! 👋 I'm the TONES Fashion AI Assistant. What are you looking for today?", products: [], reviews: [] }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return undefined;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN";

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (event) => {
      let transcript = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        transcript += event.results[index][0].transcript;
      }
      setInput(transcript.trim());
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch {
        // Recognition may already be stopped when the component unmounts.
      }
      recognitionRef.current = null;
    };
  }, []);

  const toggleVoiceInput = () => {
    if (loading) return;

    if (!voiceSupported || !recognitionRef.current) {
      setInput((current) => current);
      window.alert("Voice input is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      return;
    }

    try {
      setInput("");
      recognitionRef.current.start();
    } catch (error) {
      console.error("Could not start speech recognition:", error);
    }
  };

  const sendMessage = async (question = null) => {
    const message = (question ?? input).trim();
    if (!message || loading) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
    }

    setMessages((previous) => [...previous, { id: Date.now(), role: "user", content: message, products: [], reviews: [] }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "The AI assistant could not process the request.");

      setMessages((previous) => [
        ...previous,
        { id: Date.now() + 1, role: "assistant", content: data.answer, products: data.products || [], reviews: data.reviews || [], suggestedQuestions: data.suggested_questions || [] },
      ]);
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: error.message || "Something went wrong. Please try again.",
          products: [],
          reviews: [],
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    if (loading) return;
    try { setSessionId(crypto.randomUUID()); } catch { setSessionId(`tones-${Date.now()}-${Math.random().toString(36).slice(2)}`); }
    if (isListening && recognitionRef.current) recognitionRef.current.stop();
    setMessages([{ id: Date.now(), role: "assistant", content: "Hi! 👋 I'm the TONES Fashion AI Assistant. What are you looking for today?", products: [], reviews: [], suggestedQuestions: [] }]);
    setInput("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="assistant-page">
      <header className="assistant-header">
        <button className="brand-button" onClick={onHome}>
          <span className="brand-mark">T</span>
          <span><strong>TONES</strong><small>FASHION AI</small></span>
        </button>
        <div className="assistant-header-right">
          <div className="live-status"><i /> AI Assistant online</div>
          <button className="new-chat-button" onClick={startNewChat} disabled={loading}>＋ New Chat</button>
        </div>
      </header>

      <main className="chat-container">
        {messages.length === 1 && !loading && (
          <section className="assistant-welcome">
            <div className="welcome-orb"><span>T</span></div>
            <div>
              <div className="welcome-badge">TONES AI · RAG ASSISTANT</div>
              <h1>What can we find<br /><span>for you?</span></h1>
              <p>Ask about products, sizes, prices, shipping, returns, orders and more.</p>
            </div>
          </section>
        )}

        <section className="messages">
          {messages.map((message) => (
            <div key={message.id} className={`message-row ${message.role}`}>
              {message.role === "assistant" && <div className="assistant-avatar">T</div>}
              <div className="message-group">
                <div className={`message ${message.error ? "error-message" : ""}`}>{message.content}</div>
                {message.products?.length > 0 && (
                  <div className="product-grid">
                    {message.products.map((product, index) => (
                      <ProductCard key={`${product.url}-${index}`} product={product} />
                    ))}
                  </div>
                )}
                {message.reviews?.length > 0 && (
                  <div className="review-grid">
                    {message.reviews.map((review) => (
                      <ReviewCard key={review.review_id} review={review} />
                    ))}
                  </div>
                )}
                {message.role === "assistant" && message.suggestedQuestions?.length > 0 && (
                  <div className="message-suggestions">
                    <div className="suggestions-title">SUGGESTED QUESTIONS</div>
                    <div className="suggestion-list">
                      {message.suggestedQuestions.map((question) => (
                        <button key={question} className="suggestion-button" onClick={() => sendMessage(question)} disabled={loading}>
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="assistant-avatar">T</div>
              <div className="message typing-message"><span /><span /><span /></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </section>

        {!loading && messages.length === 1 && (
          <section className="suggestions">
            <div className="suggestions-title">TRY ASKING</div>
            <div className="suggestion-list">
              {SUGGESTED_QUESTIONS.map((question) => (
                <button key={question} className="suggestion-button" onClick={() => sendMessage(question)}>
                  {question}
                </button>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="input-area">
        <div className="input-wrapper">
          <div className="input-leading-mark" aria-hidden="true">T</div>

          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? "Listening… speak your TONES question" : "Ask TONES AI anything..."}
            rows="1"
            disabled={loading}
            aria-label="Ask TONES AI"
          />

          <button
            type="button"
            className={`voice-button ${isListening ? "is-listening" : ""}`}
            onClick={toggleVoiceInput}
            disabled={loading}
            aria-label={isListening ? "Stop voice input" : "Start voice input"}
            title={voiceSupported ? (isListening ? "Stop listening" : "Speak your question") : "Voice input is not supported in this browser"}
          >
            <span className="voice-icon" aria-hidden="true">
              {isListening ? (
                <span className="stop-icon" />
              ) : (
                <svg viewBox="0 0 24 24" focusable="false">
                  <path d="M12 15.5a3.5 3.5 0 0 0 3.5-3.5V7a3.5 3.5 0 0 0-7 0v5a3.5 3.5 0 0 0 3.5 3.5Z" />
                  <path d="M5 11.5a7 7 0 0 0 14 0M12 18.5V22M8.5 22h7" />
                </svg>
              )}
            </span>
            {isListening && <span className="voice-pulse" />}
          </button>

          <button
            className="send-button"
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            aria-label="Send message"
            title="Send message"
          >
            <span>➤</span>
          </button>
        </div>

        <div className={`voice-status ${isListening ? "active" : ""}`}>
          <span className="voice-status-dot" />
          {isListening ? "Listening — speak your question" : "Type or use the microphone to ask TONES AI"}
        </div>

        <div className="input-note"><span>●</span> TONES Fashion AI Assistant · Answers grounded in current knowledge</div>
      </footer>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState("home");
  return page === "home" ? <Home onOpenAssistant={() => setPage("assistant")} /> : <Assistant onHome={() => setPage("home")} />;
}
