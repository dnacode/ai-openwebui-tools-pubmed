"""
title: PubMed Literature Search
author: Vinay 
author_url: https://github.com/dnacode
funding_url: https://github.com/dnacode/ai-openwebui-tools-pubmed
git_url: https://github.com/dnacode/ai-openwebui-tools-pubmed
version: 1.0.0
date: 2025-04-17
license: MIT
description: Searches PubMed scientific literature database and returns formatted results with titles, authors, journals, and publication dates. Supports customizable result counts and provides direct links to articles.
"""


import requests
from typing import List, Dict, Optional
from pydantic import Field


class Tools:
    def __init__(self):
        pass

    def search_pubmed(
        self,
        query: str = Field(
            ..., description="The search query for PubMed scientific articles"
        ),
        max_results: int = Field(
            5, description="Maximum number of results to return (1-50)", ge=1, le=50
        ),
    ) -> str:
        """
        Search PubMed for scientific literature and return formatted results.
        """
        try:
            # Get article data from PubMed
            articles = self._fetch_pubmed_data(query, max_results)

            if not articles:
                return f"No PubMed results found for query: '{query}'."

            # Format the results as markdown
            return self._format_results(query, articles)

        except Exception as e:
            return f"Error in PubMed search: {str(e)}"

    def _fetch_pubmed_data(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, str]]:
        """Helper function to fetch data from PubMed API"""
        # Base URL for PubMed E-utilities
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

        # First get article IDs
        search_url = f"{base_url}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
        }
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        search_data = response.json()

        # Get article details
        article_ids = search_data["esearchresult"]["idlist"]
        if not article_ids:
            return []

        # Fetch article summaries
        fetch_url = f"{base_url}/esummary.fcgi"
        params = {"db": "pubmed", "id": ",".join(article_ids), "retmode": "json"}
        response = requests.get(fetch_url, params=params)
        response.raise_for_status()
        summaries = response.json()["result"]

        # Format results
        results = []
        for article_id in article_ids:
            article = summaries[article_id]
            results.append(
                {
                    "title": article["title"],
                    "authors": (
                        ", ".join(
                            author["name"]
                            for author in article.get("authors", [])
                            if "name" in author and author["name"]
                        )
                        if "authors" in article
                        else ""
                    ),
                    "pubdate": article.get("pubdate", ""),
                    "journal": article.get("fulljournalname", ""),
                    "doi": next(
                        (
                            id_obj["value"]
                            for id_obj in article.get("articleids", [])
                            if id_obj["idtype"] == "doi"
                        ),
                        "",
                    ),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/",
                }
            )
        return results

    def _format_results(self, query: str, articles: List[Dict[str, str]]) -> str:
        """Helper function to format search results as markdown"""
        markdown = f"# PubMed Search Results\n\n**Query:** {query}\n\n**Found:** {len(articles)} results\n\n"

        for i, article in enumerate(articles):
            markdown += f"## {i+1}. {article.get('title', 'Untitled')}\n\n"

            if article.get("authors"):
                markdown += f"**Authors:** {article['authors']}\n\n"

            journal_info = []
            if article.get("journal"):
                journal_info.append(article["journal"])
            if article.get("pubdate"):
                journal_info.append(article["pubdate"])
            if journal_info:
                markdown += f"**Published in:** {' - '.join(journal_info)}\n\n"

            if article.get("doi"):
                markdown += f"**DOI:** {article['doi']}\n\n"

            markdown += f"**PubMed Link:** [View Article]({article.get('url', '')})\n\n"

            markdown += "---\n\n"

        return markdown
