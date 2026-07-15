"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, Calendar, Tag } from "lucide-react";

export default function BlogListPage() {
  const [blogsData, setBlogsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("");

  const fetchBlogs = () => {
    setLoading(true);
    const url = activeCategory ? `/api/blogs/?category=${activeCategory}` : "/api/blogs/";
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setBlogsData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching blogs:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchBlogs();
  }, [activeCategory]);

  if (loading) {
    return <div className="p-12 text-center animate-pulse font-semibold">Loading blogs...</div>;
  }

  const categories = blogsData?.categories || [];
  const posts = blogsData?.posts || [];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 w-full flex-1 flex flex-col">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2 flex items-center justify-center gap-2">
          <BookOpen className="w-6 h-6 text-primary" /> Stay Blog
        </h1>
        <p className="text-xs text-on-surface-variant max-w-md mx-auto">Expert rental guides, neighborhood walkability tips, and tenant guidelines.</p>
      </div>

      {/* Categories filter tabs */}
      <div className="flex gap-2 justify-center border-b border-outline-variant/30 pb-3 mb-10 overflow-x-auto">
        <button
          onClick={() => setActiveCategory("")}
          className={`px-4 py-1.5 rounded-full text-xs font-bold shrink-0 transition-colors ${
            activeCategory === "" ? "bg-primary text-white" : "bg-surface-container hover:bg-outline-variant/30 text-on-surface-variant"
          }`}
        >
          All Articles
        </button>
        {categories.map((c: any) => (
          <button
            key={c.slug}
            onClick={() => setActiveCategory(c.slug)}
            className={`px-4 py-1.5 rounded-full text-xs font-bold shrink-0 transition-colors ${
              activeCategory === c.slug ? "bg-primary text-white" : "bg-surface-container hover:bg-outline-variant/30 text-on-surface-variant"
            }`}
          >
            {c.name}
          </button>
        ))}
      </div>

      {/* Blogs catalog list */}
      {posts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {posts.map((p: any, idx: number) => (
            <Link href={`/blog/${p.slug}`} key={idx} className="bg-white rounded-2xl overflow-hidden property-card-shadow group border border-outline-variant/30 flex flex-col transition-all duration-300 hover:-translate-y-1">
              <div className="relative h-48 bg-surface-container-high overflow-hidden shrink-0">
                {p.image ? (
                  <img src={p.image} alt={p.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl">📝</div>
                )}
              </div>
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-4 text-[10px] text-text-muted mb-2 font-bold">
                    <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {new Date(p.created_at).toLocaleDateString()}</span>
                    {p.category && <span className="flex items-center gap-1"><Tag className="w-3.5 h-3.5" /> {p.category}</span>}
                  </div>
                  <h3 className="text-sm font-bold text-on-surface mb-2 line-clamp-2 group-hover:text-primary transition-colors">{p.title}</h3>
                  <p className="text-xs text-on-surface-variant line-clamp-3 leading-relaxed">{p.summary}</p>
                </div>
                <div className="pt-4 mt-4 border-t border-outline-variant/30 text-[11px] font-bold text-primary flex items-center gap-1">
                  Read Full Article &rarr;
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-white border border-outline-variant rounded-2xl">
          <p className="text-xs text-on-surface-variant font-medium">No articles found in this category.</p>
        </div>
      )}
    </div>
  );
}
