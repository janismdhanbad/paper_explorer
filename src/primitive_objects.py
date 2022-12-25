import requests
from typing import List, Dict
from data.secret_key import SemanticScholarCreds

SEMSCH_LINK = "https://api.semanticscholar.org/graph/v1"


class Authors:
    def __init__(
        self,
        id: str=None,
        name=None,
        homepage=None,
        paper_count=None,
        citations=None,
        hindex=None,
        papers=None,
        worked_with=None,
        cache_file=None,
    ):

        if cache_file is None:

            self.id = id
            self.name = name
            self.homepage = homepage
            self.paper_count = paper_count
            self.citations = citations
            self.hindex = hindex
            self.papers = papers
            self.worked_with = worked_with
        else:
            self.id = cache_file["id"]
            self.name = cache_file["name"]
            self.homepage = cache_file["homepage"]
            self.paper_count = cache_file["paper_count"]
            self.citations = cache_file["citations"]
            self.hindex = cache_file["hindex"]
            self.papers = cache_file["papers"]
            self.worked_with = cache_file["worked_with"]


class Paper:
    def __init__(
        self,
        id: str=None,
        arxiv_id: str=None,
        title: str=None,
        authors: List[str]=None,
        abstract: str=None,
        primary_category: str=None,
        secondary_category: str=None,
        cache_file: Dict=None,
    ):
        if cache_file is None:

            self.id = id
            self.title = title
            self.authors = authors
            self.abstract = abstract
            self.arxiv_id = arxiv_id
            self.primary_category = primary_category
            self.secondary_category = secondary_category
        else:
            self.id = cache_file["id"]
            self.title = cache_file["title"]
            self.authors = cache_file["authors"]
            self.abstract = cache_file["abstract"]
            self.primary_category = cache_file["primary_category"]
            self.secondary_category = cache_file["secondary_category"]
            self.arxiv_id = cache_file["arxiv_id"]


class ArxivPaper(Paper):
    def __init__(
        self,
        id: str=None,
        arxiv_id: str=None,
        title: str=None,
        authors: List[str]=None,
        abstract: str=None,
        primary_category: str=None,
        secondary_category: str=None,
        cache_file: Dict=None,
    ):
        super().__init__(id, arxiv_id, title, authors, abstract, primary_category,secondary_category, cache_file)
        

    def update_semsch_id(self):
        arxiv_id = self.arxiv_id
        arxiv_id = arxiv_id.replace("abs/", "").split("v")[0]
        url = f"{SEMSCH_LINK}/paper/arXiv:{arxiv_id}"
        res = requests.get(url, headers={"x-api-key": SemanticScholarCreds.API_KEY})
        response = res.json()
        if response.get("paperId"):
            self.id = res.json()["paperId"]
        else:
            self.id = None
            self.title = self.title + " (Unfortunately, this paper is not available on semantic scholar so you can't explore it further) :/ "


class ArxivID:
    def __init__(self, ar_id: str):
        self.id = ar_id


class SemSchPaper(Paper):
    def __init__(
        self,
        id: str=None,
        arxiv_id: str=None,
        title: str=None,
        authors: List[str]=None,
        abstract: str=None,
        primary_category: str=None,
        secondary_category: str=None,
        year: str=None,
        reference_count: str=None,
        citation_count: str=None,
        influential_paper_citations: str=None,
        is_open_access: bool=None,
        citations: List[str]=None,
        references: List[str] =None,
        url: str=None,
        cache_file: Dict=None,
    ):
        super().__init__(id, arxiv_id, title, authors, abstract, primary_category,secondary_category, cache_file)

        if cache_file is None:

            self.year = year
            self.reference_count = reference_count
            self.citation_count = citation_count
            self.influential_paper_citations = influential_paper_citations
            self.is_open_access = is_open_access
            self.citations = citations
            self.references = references
            self.url = url

        else:
            self.year = cache_file["year"]
            self.reference_count = cache_file["reference_count"]
            self.citation_count = cache_file["citation_count"]
            self.influential_paper_citations = cache_file["influential_paper_citations"]
            self.is_open_access = cache_file["is_open_access"]
            self.citations = cache_file["citations"]
            self.references = cache_file["references"]
            self.url = cache_file["url"]


class Categories:
    def __init__(self, category_name=None, paper_ids=None, cache_file=None):
        if cache_file is None:
            self.category_name = category_name
            self.paper_ids = paper_ids
        else:
            self.category_name = cache_file["category"]
            self.paper_ids = paper_ids


class TwitterData:
    def __init__(
        self, paper_id, text, retweet_count, reply_count, like_count, quote_count
    ):
        self.paper_id = paper_id
        self.text = text
        self.like_count = like_count
        self.retweet_count = retweet_count
        self.reply_count = reply_count
        self.quote_count = quote_count
