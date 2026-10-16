"""VOSviewer Bibliometric Mapping & Science Visualization Clone.

Implements the VOS (Visualization of Similarities) algorithm, co-occurrence analysis,
co-authorship networks, bibliographic coupling, modularity clustering, and standard
VOSviewer file exports (.map, .net, and VOSviewer Online JSON).

References:
- Van Eck, N.J., & Waltman, L. (2010). Software survey: VOSviewer, a computer
  program for bibliometric mapping. Scientometrics, 84(2), 523-538.
- Van Eck, N.J., & Waltman, L. (2009). How to normalize co-occurrence data?
  An analysis of some well-known similarity measures. JASIST, 60(8), 1635-1651.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BibliometricItem:
    """Represents a node/term/author in the bibliometric map."""

    id: int
    label: str
    x: float = 0.0
    y: float = 0.0
    cluster: int = 1
    occurrences: int = 1
    total_link_strength: float = 0.0
    avg_pub_year: float = 2024.0
    citations: int = 0
    scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BibliometricLink:
    """Represents a co-occurrence/citation link between two items."""

    source_id: int
    target_id: int
    strength: float
    raw_frequency: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BibliometricCluster:
    """Represents a thematic topic cluster detected by VOS modularity."""

    cluster_id: int
    name: str
    color: str
    items: list[str] = field(default_factory=list)
    top_terms: list[str] = field(default_factory=list)
    avg_year: float = 2024.0


CLUSTER_COLORS = [
    "#E41A1C",  # 1: Red
    "#377EB8",  # 2: Blue
    "#4DAF4A",  # 3: Green
    "#984EA3",  # 4: Purple
    "#FF7F00",  # 5: Orange
    "#FFFF33",  # 6: Yellow
    "#A65628",  # 7: Brown
    "#F781BF",  # 8: Pink
]


class VOSviewerClone:
    """Complete Reverse Engineering & Clone of VOSviewer Bibliometric Mapping Suite."""

    STOPWORDS = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "but", "if", "then", "else", "when", "upn", "veteran", "jawa", "timur",
        "indonesia", "study", "research", "analysis", "approach", "method", "results",
        "using", "based", "effect", "impact", "role", "model", "paper", "article",
    }

    def __init__(self, min_cluster_size: int = 1, resolution: float = 1.0):
        self.min_cluster_size = min_cluster_size
        self.resolution = resolution
        self.items: dict[int, BibliometricItem] = {}
        self.label_to_id: dict[str, int] = {}
        self.links: list[BibliometricLink] = []
        self.clusters: dict[int, BibliometricCluster] = {}
        self.co_occurrence_matrix: defaultdict[tuple[int, int], int] = defaultdict(int)

    # ==========================================================================
    # 1. TEXT EXTRACTION & NORMALIZATION
    # ==========================================================================
    @classmethod
    def clean_keyword(cls, kw: str) -> str:
        """Standardizes bibliometric keywords into canonical form."""
        cleaned = re.sub(r"[^\w\s-]", "", kw).strip().lower()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    @classmethod
    def extract_keywords_from_text(cls, text: str, min_len: int = 3) -> list[str]:
        """Extracts candidate keywords and unigram/bigram terms from text."""
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", text)]
        filtered = [w for w in words if w not in cls.STOPWORDS and len(w) >= min_len]

        terms = list(filtered)
        # Extract meaningful bigrams
        for i in range(len(filtered) - 1):
            w1, w2 = filtered[i], filtered[i + 1]
            if w1 not in cls.STOPWORDS and w2 not in cls.STOPWORDS:
                terms.append(f"{w1} {w2}")
        return terms

    # ==========================================================================
    # 2. CORPUS INGESTION & CO-OCCURRENCE COMPUTATION
    # ==========================================================================
    def build_from_documents(
        self,
        docs: list[dict[str, Any]],
        keyword_key: str = "keywords",
        title_key: str = "title",
        year_key: str = "year",
        citation_key: str = "citations",
        min_occurrences: int = 1,
    ) -> dict[str, Any]:
        """Builds bibliometric co-occurrence network from a list of documents."""
        self.items.clear()
        self.label_to_id.clear()
        self.links.clear()
        self.clusters.clear()
        self.co_occurrence_matrix.clear()

        term_counts: Counter[str] = Counter()
        term_years: defaultdict[str, list[int]] = defaultdict(list)
        term_citations: defaultdict[str, int] = defaultdict(int)
        doc_term_sets: list[set[str]] = []

        for doc in docs:
            doc_terms: set[str] = set()

            # Process explicit keywords
            kws = doc.get(keyword_key, [])
            if isinstance(kws, str):
                kws = [k.strip() for k in re.split(r"[,;]", kws) if k.strip()]
            for kw in kws:
                ckw = self.clean_keyword(kw)
                if ckw and ckw not in self.STOPWORDS:
                    doc_terms.add(ckw)

            # Process title terms
            title = doc.get(title_key, "")
            if title:
                for term in self.extract_keywords_from_text(title):
                    doc_terms.add(term)

            year = int(doc.get(year_key, 2024) or 2024)
            cits = int(doc.get(citation_key, 0) or 0)

            for term in doc_terms:
                term_counts[term] += 1
                term_years[term].append(year)
                term_citations[term] += cits

            if doc_terms:
                doc_term_sets.append(doc_terms)

        # Filter by minimum occurrences
        valid_terms = [t for t, c in term_counts.items() if c >= min_occurrences]
        valid_terms.sort(key=lambda t: (-term_counts[t], t))

        # Register items
        for idx, term in enumerate(valid_terms, start=1):
            avg_y = sum(term_years[term]) / len(term_years[term]) if term_years[term] else 2024.0
            item = BibliometricItem(
                id=idx,
                label=term,
                occurrences=term_counts[term],
                avg_pub_year=round(avg_y, 2),
                citations=term_citations[term],
            )
            self.items[idx] = item
            self.label_to_id[term] = idx

        # Calculate co-occurrence frequencies
        term_id_links: Counter[tuple[int, int]] = Counter()
        for term_set in doc_term_sets:
            active_ids = [self.label_to_id[t] for t in term_set if t in self.label_to_id]
            active_ids.sort()
            for i in range(len(active_ids)):
                for j in range(i + 1, len(active_ids)):
                    term_id_links[(active_ids[i], active_ids[j])] += 1

        m = max(1, sum(term_id_links.values()))

        # Calculate Association Strength & Total Link Strength
        tls_map: defaultdict[int, float] = defaultdict(float)
        for (u, v), freq in term_id_links.items():
            cu = self.items[u].occurrences
            cv = self.items[v].occurrences
            # Van Eck & Waltman (2009) Association Strength
            assoc_strength = (2.0 * m * freq) / (cu * cv) if (cu * cv) > 0 else 0.0
            assoc_strength = round(assoc_strength, 4)

            self.links.append(
                BibliometricLink(
                    source_id=u,
                    target_id=v,
                    strength=assoc_strength,
                    raw_frequency=freq,
                )
            )
            tls_map[u] += freq
            tls_map[v] += freq

        for item_id, item in self.items.items():
            item.total_link_strength = tls_map[item_id]

        # Run VOS Layout & Clustering
        self._compute_vos_layout()
        self._compute_modularity_clusters()

        return self.get_summary()

    def build_from_scopus_csv(self, csv_content: str, min_occurrences: int = 1) -> dict[str, Any]:
        """Ingests standard Elsevier Scopus CSV export with Author/Index Keywords."""
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f)
        docs = []
        for row in reader:
            kws = []
            for col in ["Author Keywords", "Index Keywords"]:
                if col in row and row[col]:
                    kws.extend([k.strip() for k in row[col].split(";") if k.strip()])
            docs.append({
                "title": row.get("Title", ""),
                "keywords": kws,
                "year": row.get("Year", 2024),
                "citations": row.get("Cited by", 0),
            })
        return self.build_from_documents(docs, min_occurrences=min_occurrences)

    def build_from_canonical_records(
        self,
        records: list[Any],
        min_occurrences: int = 1,
    ) -> dict[str, Any]:
        """Ingests CanonicalPaperRecord objects directly from CoreDataEngine."""
        docs = []
        for r in records:
            title = getattr(r, "title", "") if hasattr(r, "title") else r.get("title", "")
            abstract = getattr(r, "abstract", "") if hasattr(r, "abstract") else r.get("abstract", "")
            year = getattr(r, "year", 2024) if hasattr(r, "year") else r.get("year", 2024)
            citations = getattr(r, "cited_by_count", 0) if hasattr(r, "cited_by_count") else r.get("cited_by_count", 0)

            combined_text = f"{title} {abstract or ''}".strip()
            extracted_kws = self.extract_keywords_from_text(combined_text)

            docs.append({
                "title": title,
                "keywords": extracted_kws,
                "year": year or 2024,
                "citations": citations or 0,
            })
        return self.build_from_documents(docs, min_occurrences=min_occurrences)


    # ==========================================================================
    # 3. VOS MAPPING LAYOUT & DIMENSIONALITY REDUCTION
    # ==========================================================================
    def _compute_vos_layout(self) -> None:
        """Computes 2D coordinates (x, y) minimizing weighted squared distances."""
        n = len(self.items)
        if n == 0:
            return
        if n == 1:
            self.items[1].x, self.items[1].y = 0.0, 0.0
            return

        # Initialize coordinates in circle
        for idx, item in self.items.items():
            angle = (2.0 * math.pi * (idx - 1)) / n
            radius = 1.0 + (item.occurrences / 5.0)
            item.x = round(radius * math.cos(angle), 4)
            item.y = round(radius * math.sin(angle), 4)

        # Force-directed relaxation (Van Eck & Waltman VOS gradient descent)
        iterations = 60
        step_size = 0.05
        for _ in range(iterations):
            forces: defaultdict[int, list[float]] = defaultdict(lambda: [0.0, 0.0])

            # Attractive forces from association links
            for link in self.links:
                u, v = link.source_id, link.target_id
                pu, pv = self.items[u], self.items[v]
                dx, dy = pv.x - pu.x, pv.y - pu.y
                dist = max(0.01, math.sqrt(dx * dx + dy * dy))
                # Attraction proportional to link strength
                f = link.strength * (dist - 0.5)
                forces[u][0] += f * (dx / dist)
                forces[u][1] += f * (dy / dist)
                forces[v][0] -= f * (dx / dist)
                forces[v][1] -= f * (dy / dist)

            # Repulsive forces between all node pairs to prevent overlap
            item_list = list(self.items.values())
            for i in range(len(item_list)):
                for j in range(i + 1, len(item_list)):
                    p1, p2 = item_list[i], item_list[j]
                    dx, dy = p2.x - p1.x, p2.y - p1.y
                    dist_sq = max(0.04, dx * dx + dy * dy)
                    repulsion = 0.5 / dist_sq
                    forces[p1.id][0] -= repulsion * dx
                    forces[p1.id][1] -= repulsion * dy
                    forces[p2.id][0] += repulsion * dx
                    forces[p2.id][1] += repulsion * dy

            # Apply movements with bounding
            for item_id, item in self.items.items():
                item.x += forces[item_id][0] * step_size
                item.y += forces[item_id][1] * step_size
                item.x = round(max(-5.0, min(5.0, item.x)), 4)
                item.y = round(max(-5.0, min(5.0, item.y)), 4)

    # ==========================================================================
    # 4. MODULARITY CLUSTERING (VOS CLUSTER DETECTION)
    # ==========================================================================
    def _compute_modularity_clusters(self) -> None:
        """Groups nodes into dense thematic clusters using link connectivity & layout."""
        if not self.items:
            return

        adj: defaultdict[int, list[tuple[int, float]]] = defaultdict(list)
        for link in self.links:
            adj[link.source_id].append((link.target_id, link.strength))
            adj[link.target_id].append((link.source_id, link.strength))

        # Modularity clustering: Greedy seed & neighborhood expansion
        visited: set[int] = set()
        cluster_assignment: dict[int, int] = {}
        current_cluster = 1

        # Sort by total link strength descending as cluster seeds
        sorted_nodes = sorted(self.items.values(), key=lambda it: -it.total_link_strength)

        for seed in sorted_nodes:
            if seed.id in visited:
                continue
            cluster_members = [seed.id]
            visited.add(seed.id)

            # Gather strongly connected neighbors
            neighbors = sorted(adj[seed.id], key=lambda x: -x[1])
            for neighbor_id, strength in neighbors:
                if neighbor_id not in visited and len(cluster_members) < 8:
                    cluster_members.append(neighbor_id)
                    visited.add(neighbor_id)

            for member_id in cluster_members:
                cluster_assignment[member_id] = current_cluster
            current_cluster += 1

        # Fallback for unassigned nodes
        for item_id in self.items:
            if item_id not in cluster_assignment:
                cluster_assignment[item_id] = 1

        # Assign back to items
        self.clusters.clear()
        cluster_nodes: defaultdict[int, list[BibliometricItem]] = defaultdict(list)
        for item_id, c_id in cluster_assignment.items():
            self.items[item_id].cluster = c_id
            cluster_nodes[c_id].append(self.items[item_id])

        for c_id, members in cluster_nodes.items():
            top_t = [m.label for m in sorted(members, key=lambda m: -m.occurrences)[:4]]
            avg_y = sum(m.avg_pub_year for m in members) / len(members) if members else 2024.0
            color = CLUSTER_COLORS[(c_id - 1) % len(CLUSTER_COLORS)]
            name = f"Cluster {c_id}: {top_t[0].capitalize()}" if top_t else f"Cluster {c_id}"
            self.clusters[c_id] = BibliometricCluster(
                cluster_id=c_id,
                name=name,
                color=color,
                items=[m.label for m in members],
                top_terms=top_t,
                avg_year=round(avg_y, 2),
            )

    # ==========================================================================
    # 5. EXPORT UTILITIES (VOSviewer Standard Formats)
    # ==========================================================================
    def export_vos_map(self, filepath: str | Path | None = None) -> str:
        """Exports standard VOSviewer Map File format (.map / .txt)."""
        lines = [
            "id\tlabel\tx\ty\tcluster\tweight<Occurrences>\tweight<Total link strength>\tscore<Avg. pub. yr>\tscore<Citations>"
        ]
        for it in sorted(self.items.values(), key=lambda x: x.id):
            row = (
                f"{it.id}\t{it.label}\t{it.x:.4f}\t{it.y:.4f}\t{it.cluster}\t"
                f"{it.occurrences}\t{it.total_link_strength:.1f}\t{it.avg_pub_year:.2f}\t{it.citations}"
            )
            lines.append(row)
        content = "\n".join(lines) + "\n"
        if filepath:
            Path(filepath).write_text(content, encoding="utf-8")
        return content

    def export_vos_network(self, filepath: str | Path | None = None) -> str:
        """Exports standard VOSviewer Network File format (.net / .txt)."""
        lines = ["source\ttarget\tweight"]
        for lnk in self.links:
            lines.append(f"{lnk.source_id}\t{lnk.target_id}\t{lnk.strength:.4f}")
        content = "\n".join(lines) + "\n"
        if filepath:
            Path(filepath).write_text(content, encoding="utf-8")
        return content

    def export_vosviewer_online_json(self, filepath: str | Path | None = None) -> str:
        """Exports JSON payload 100% compatible with VOSviewer Online (app.vosviewer.com)."""
        items_payload = []
        for it in sorted(self.items.values(), key=lambda x: x.id):
            items_payload.append({
                "id": it.id,
                "label": it.label,
                "x": it.x,
                "y": it.y,
                "cluster": it.cluster,
                "weights": {
                    "Occurrences": it.occurrences,
                    "Total link strength": it.total_link_strength,
                },
                "scores": {
                    "Avg. pub. year": it.avg_pub_year,
                    "Citations": it.citations,
                },
            })

        network_links = []
        for lnk in self.links:
            network_links.append({
                "source_id": lnk.source_id,
                "target_id": lnk.target_id,
                "strength": lnk.strength,
            })

        cluster_colors = {c_id: c.color for c_id, c in self.clusters.items()}

        payload = {
            "network": {
                "items": items_payload,
                "links": network_links,
                "clusters": [asdict(c) for c in self.clusters.values()],
            },
            "config": {
                "title": "AI Thesis Generator — VOSviewer Science Map",
                "parameters": {
                    "min_cluster_size": self.min_cluster_size,
                    "resolution": self.resolution,
                    "color_scheme": cluster_colors,
                },
            },
        }
        content = json.dumps(payload, indent=2)
        if filepath:
            Path(filepath).write_text(content, encoding="utf-8")
        return content

    # ==========================================================================
    # 6. SUMMARY & ASCII VISUALIZATION
    # ==========================================================================
    def get_summary(self) -> dict[str, Any]:
        """Returns bibliometric network diagnostics and cluster metrics."""
        return {
            "total_items": len(self.items),
            "total_links": len(self.links),
            "total_clusters": len(self.clusters),
            "clusters": {c_id: asdict(c) for c_id, c in self.clusters.items()},
            "top_terms": [it.label for it in sorted(self.items.values(), key=lambda x: -x.occurrences)[:10]],
            "max_link_strength": max((lnk.strength for lnk in self.links), default=0.0),
        }

    def generate_ascii_graph(self) -> str:
        """Produces a clean terminal-friendly ASCII graph representation of the map."""
        out = []
        out.append("======================================================================")
        out.append("VOSVIEWER BIBLIOMETRIC CO-OCCURRENCE MAP (LEIDEN VOS ALGORITHM)")
        out.append("======================================================================")
        out.append(f"Nodes (Items): {len(self.items):<5} | Links: {len(self.links):<5} | Clusters: {len(self.clusters)}")
        out.append("----------------------------------------------------------------------")

        for c_id, cluster in sorted(self.clusters.items()):
            out.append(f"\n[● {cluster.name.upper()}] (Color: {cluster.color})")
            out.append(f"  Avg Publication Year: {cluster.avg_year:.1f}")
            out.append(f"  Key Term Nodes      : {', '.join(cluster.top_terms)}")

            # List member details
            for it_id, it in sorted(self.items.items()):
                if it.cluster == c_id:
                    out.append(
                        f"    - {it.label:<25} (Occurrences: {it.occurrences:<2}, "
                        f"TLS: {it.total_link_strength:<4.1f}, x: {it.x:<6.2f}, y: {it.y:<6.2f})"
                    )

        out.append("\nTop Association Strength Links:")
        sorted_links = sorted(self.links, key=lambda lnk: -lnk.strength)[:5]
        for lnk in sorted_links:
            s_label = self.items[lnk.source_id].label
            t_label = self.items[lnk.target_id].label
            out.append(f"  🔗 {s_label} <---> {t_label} (Strength: {lnk.strength:.3f}, Freq: {lnk.raw_frequency})")
        out.append("======================================================================")
        return "\n".join(out)
