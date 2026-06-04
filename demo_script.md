# 🎥 Neusearch AI - Demo Video Script (2-3 Minutes)

**Goal:** Showcase the product's functionality, technical depth, and user experience to a recruiter.

---

## 0:00 - 0:30 | Introduction & The "Why"
**(Camera on you or Split screen with Landing Page)**

"Hi, I'm [Your Name], and this is **Neusearch AI**—an intelligent product discovery assistant I built to solve a common problem in e-commerce: **Search is often too rigid.**

Most sites force you to search for keywords like 'shampoo' or 'conditioner'. But what if you have a specific problem, like 'I have dry hair and dandruff'? Standard search fails there.

Neusearch AI bridges that gap using **Semantic Search** and **RAG (Retrieval-Augmented Generation)** to understand *intent*, not just keywords."

---

## 0:30 - 1:30 | The Walkthrough (Product in Action)
**(Screen share: Frontend Application)**

**1. The Storefront (Home Page)**
"Here’s the main interface. It’s a modern, responsive React application styled with Tailwind CSS.
-   You can see the product grid here.
-   All this data—images, titles, prices—was **custom scraped** from a live health website (Traya) using a Python script I wrote. It’s not dummy data."

**2. Product Details**
*(Click on a product, e.g., 'Anti-Dandruff Shampoo')*
"Clicking into a product, we see the full details.
-   We have the description, key features, and price.
-   This layout is designed to be clean and conversion-focused."

**3. The AI Assistant (The Core Feature)**
*(Navigate to 'AI Assistant' tab)*
"Now, let’s look at the coolest part. Instead of browsing, I’ll ask the AI for help.
-   *Type:* **'I've been noticing a lot of hair fall lately. What should I use?'**
-   *Click Send.*

*(Wait for response)*

"Boom. It didn't just give me a random list. It understood 'hair fall' and retrieved the specific products tagged for hair defense and scalp health.
-   It uses **hybrid retrieval** (Qdrant dense search plus BM25 and RRF) to find products that match both intent and keywords.
-   It then ranks them and presents them to me."

---

## 1:30 - 2:15 | Under the Hood (Architecture)
**(Screen share: VS Code / Architecture Diagram / README)**

"Briefly, here’s how it works under the hood:
1.  **Data Pipeline:** I built a scraper using `BeautifulSoup` to fetch data and clean it.
2.  **Vector Database:** Product data is embedded using `sentence-transformers`, stored in **Qdrant**, fused with BM25 results, and cross-encoder reranked.
3.  **Backend:** The API is built with **FastAPI**. When I send a query, it converts my text to a vector, finds the nearest neighbors in the database, and returns the results.
4.  **Frontend:** The UI is **React** with **Vite**, ensuring it's fast and snappy."

---

## 2:15 - 2:30 | Conclusion
**(Camera on you)**

"Neusearch AI demonstrates how we can move beyond keyword search to build truly helpful e-commerce experiences.
-   It’s fully containerized with **Docker** for easy deployment.
-   You can check out the code and the detailed README on my GitHub.

Thanks for watching!"
