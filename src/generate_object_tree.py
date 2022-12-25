import sys

sys.path.append("../")
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import requests
from data.secret_key import SemanticScholarCreds

import utils
from primitive_objects import ArxivID, ArxivPaper, Authors, SemSchPaper

SEMSCH_PAPER_KEYS = [
    "id",
    "paper_arxiv_id",
    "title",
    "authors",
    "abstract",
    "category",
    "year",
    "reference_count",
    "citation_count",
    "influential_paper_citations",
    "is_open_access",
]
SEMSCH_LINK = "https://api.semanticscholar.org/graph/v1"
ARXIV_KEYS = ["arxiv_id", "title", "authors", "abstract"]
ARXIV_LINK = "http://export.arxiv.org/api/query?search_query="
NAMESPACE = {"n": "http://www.w3.org/2005/Atom"}


class SemSchTree:
    def __init__(self, cache_pth: str):
        self.cache_pth = cache_pth
        self.papers_dict = {}
        self.read_cache()

    def read_cache(self) -> None:
        """A function that reads the cache from the given input path JSON. It
        appends the result in the dictionary self.papers_dict. Note that this
        function reads a JSON that consists of papers from semantic scholar API
        """
        try:
            with open(self.cache_pth, "r") as f:
                data = json.load(f)
            if bool(data):
                for k, v in data.items():
                    self.papers_dict[k] = SemSchPaper(**v)
        except:
            pass

    def write_cache(self) -> bool:
        """The function writes cache for papers from semantic scholar API. It
        takes the dictionary self.paper_dict and writes down each paper with
        a given ID

        Returns
        -------
        bool
            Returns True if the data is successfully written to the disk, False
            otherwise
        """
        data_save = {}
        try:
            for paper_id, val in self.papers_dict.items():
                temp_dict = vars(val)
                data_save[paper_id] = temp_dict

            with open(self.cache_pth, "w") as f:
                json.dump(data_save, f)
            return True
        except:
            return False

    def get_paper_list(self) -> List[str]:
        """Returns a list of paper IDs that are present in the current cache

        Returns
        -------
        List[str]
            List of semantic scholar paper IDs
        """
        return list(self.papers_dict.keys())

    def get_arxiv_paper_list(self) -> List[str]:
        """The function returns the list of arxiv ID strings that are present in
        the cached dict.

        Returns
        -------
        List[str]
            List of Arxiv IDs
        """
        vals_arxiv = self.papers_dict.values()
        vals_arxiv = [f["arxiv_id"] for f in vals_arxiv]
        return vals_arxiv

    def get_semschID_for_arxivID(self, arxiv_id: str) -> str:
        """The function returns the semantic scholar ID for the paper given the
        Arxiv paper ID.

        Parameters
        ----------
        arxiv_id : str
            Arxiv ID for the paper

        Returns
        -------
        str
            Semantic scholar ID for the paper
        """
        url = f"{SEMSCH_LINK}/paper/arXiv:{arxiv_id}"
        res = requests.get(url, headers={"x-api-key": SemanticScholarCreds.API_KEY})
        semsch_paperid = res.json()["paperId"]
        return semsch_paperid

    def update_paper_data(self, input_id: str) -> str:
        """The function takes in paper ID and returns the semantic scholar paper
        ID for the paper. Note that the input ID can be a Arxiv ID or a semantic
        scholar ID here.

        Parameters
        ----------
        input_id : str
            Input ID, the semantic scholar ID

        Returns
        -------
        str
            Returns the semantic scholar paper ID
        """
        semsch_paperid = input_id

        # Get the current list of semantic scholar paper IDs in the cache list
        paper_list = self.get_paper_list()

        # If the ID is already present in the paper, then do not request the
        # semantic scholar API
        if semsch_paperid in paper_list:
            pass
        else:
            # Request the semantic scholar API if the ID is not present in the
            # cache

            # author fields needed in the request
            author_fields = (
                "authors.name,authors.hIndex,authors.paperCount,authors.citationCount"
            )

            # Citation fields needed in the request
            citations_fields = "citations.title,citations.influentialCitationCount"

            # General fields needed in the request
            req_fields = f"""url,title,{author_fields},abstract,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,fieldsOfStudy,{citations_fields},references&limit=50"""

            # Constructing the URl to request the semantic scholar API. Note that
            # we use the secret key from SemanticScholarCreds.API_KEY here
            url_paper = f"{SEMSCH_LINK}/paper/{semsch_paperid}?fields={req_fields}"
            _results = requests.get(
                url_paper, headers={"x-api-key": SemanticScholarCreds.API_KEY}
            )
            results = _results.json()

            # Updating the current cache using the results for the paper
            self.update_paper_info(results, semsch_paperid)
        return semsch_paperid

    def update_paper_info(self, results: Dict, semsch_paperid: str) -> None:
        """The function updates the self.paper_dict dictionary by appending the
        results of the given paper.

        Parameters
        ----------
        results : Dict
            A dictionary that is response of paper details from semantic scholar
            API
        arxiv_id : Union[ArxivID, None]
            Arxiv ID of the paper
        semsch_paperid : str
            Semantic scholar ID of the paper
        """

        # Initializing dict from results that will be used to initialize the
        # class SemSchPaper
        _initialize_dict = {}

        _initialize_dict["id"] = results["paperId"]
        _initialize_dict["arxiv_id"] = None
        _initialize_dict["title"] = results["title"]
        _initialize_dict["authors"] = results["authors"]
        _initialize_dict["abstract"] = results["abstract"]
        # _initialize_dict["category"] = None
        _initialize_dict["year"] = results["year"]
        _initialize_dict["reference_count"] = results["referenceCount"]
        _initialize_dict["citation_count"] = results["citationCount"]
        _initialize_dict["influential_paper_citations"] = results[
            "influentialCitationCount"
        ]
        _initialize_dict["is_open_access"] = results["isOpenAccess"]
        _initialize_dict["url"] = results["url"]

        citations = [f for f in results["citations"] if f["paperId"] is not None]
        citations = [f for f in citations if f["influentialCitationCount"] is not None]
        citations = sorted(
            [f for f in citations],
            key=lambda x: x["influentialCitationCount"],
            reverse=True,
        )
        citations = [f["paperId"] for f in citations][:10]
        references = [f["paperId"] for f in results["references"]]
        citations = [f for f in citations if f is not None]
        references = [f for f in references if f is not None]

        _initialize_dict["citations"] = citations
        _initialize_dict["references"] = references
        paper = SemSchPaper(**_initialize_dict)
        self.papers_dict[results["paperId"]] = paper

        # Note that there is a bug in semantic scholar paper API. sometimes, the
        # original semsch_paperid can be different from the paperId return from
        # the API request and in that case we make duplicate paper records for
        # the two separate papers IDs
        if semsch_paperid != results["paperId"]:
            self.papers_dict[semsch_paperid] = paper

    def update_papers(self, paper_ids: List[str]) -> None:
        """The function is a helper function to update the citations and references
        of a paper. It takes the list of semantic scholar paper IDs and appends
        the pertaining paper details to the python dictionary self.papers_dict

        Parameters
        ----------
        paper_ids : List[str]
            List of semantic scholar paper IDs
        """

        i = 1
        for ref_id in paper_ids:
            if self.papers_dict.get(ref_id):
                pass
            else:
                self.update_paper_data(ref_id)
                i = i + 1
                # Using time.sleep to reduce the chances of overloading the API
                # with requests
                if i % 98 == 0:
                    time.sleep(1.0)

    def fetch_paper_data(
        self, input_id: Union[ArxivID, str]
    ) -> Tuple[str, str, str, str, str, str, str, List[Dict], List[Dict]]:
        """The function is the main controlling function to create the paper
        tree. it is used inside src/app.py to extract all the details of the
        paper, i.e., paper.title, paper.authors, paper.abstract, paper.reference_count,
        paper.citation_count, paper.influential_paper_citations, paper.url,
        paper.references, paper.citation_list

        Parameters
        ----------
        input_id : Union[ArxivID, str]
            Input ID for the paper

        Returns
        -------
        Tuple[str,str,str,str,str,str,str,List[Dict], List[Dict]]
            paper.title, paper.authors, paper.abstract, paper.reference_count,
        paper.citation_count, paper.influential_paper_citations, paper.url,
        paper.references, paper.citation_list in that order
        """
        semsch_paperid = self.update_paper_data(input_id)
        paper = self.papers_dict[semsch_paperid]
        references = paper.references
        citations = paper.citations
        references = [f for f in references if f is not None]
        citations = [f for f in citations if f is not None]
        self.update_papers(references)
        self.update_papers(citations)
        reference_list = []
        citation_list = []
        self.write_cache()

        for ref in references:
            reference_list.append(vars(self.papers_dict[ref]))

        for cit in citations:
            citation_list.append(vars(self.papers_dict[cit]))

        df = pd.read_csv("../data/prev_searches.csv")
        columns_csv = [
            "paper_id",
            "Title",
            "citation_count",
            "reference_count",
            "influencial_citations_count",
        ]
        temp_df = pd.DataFrame(index=range(1), columns=columns_csv)
        temp_df["paper_id"] = paper.id
        temp_df["Title"] = paper.title
        temp_df["citation_count"] = paper.citation_count
        temp_df["reference_count"] = paper.reference_count
        temp_df["influencial_citations_count"] = paper.influential_paper_citations
        df = pd.concat([df, temp_df])
        df.to_csv("../data/prev_searches.csv", index=False)

        return (
            paper.title,
            paper.authors,
            paper.abstract,
            paper.reference_count,
            paper.citation_count,
            paper.influential_paper_citations,
            paper.url,
            reference_list,
            citation_list,
        )


class ArxivTree:
    def __init__(self, cache_pth: str):
        self.cache_pth = cache_pth
        self.papers_dict = {}
        self.read_cache()

    def read_cache(self) -> None:
        """The function reads the cache data for arxiv paper search, which is the
        first API hit that happens on the user input
        """
        try:
            with open(self.cache_pth, "r") as f:
                data = json.load(f)
            if bool(data):
                for k, v in data.items():
                    self.papers_dict[k] = ArxivPaper(**v)
        except:
            pass

    def write_cache(self) -> bool:
        """The function writes the data for Arxiv paper search

        Returns
        -------
        bool
            A bool that is True when the data is written successfully, False
            otherwise
        """
        data_save = {}
        try:

            for id_ar, paper in self.papers_dict.items():
                temp_dict = vars(paper)
                data_save[id_ar] = temp_dict

            with open(self.cache_pth, "w") as f:
                json.dump(data_save, f)
            return True
        except:
            return False

    def get_paper_titles(self) -> List[str]:
        """The function returns the list of Arxiv paper IDs that are present
        in the cache

        Returns
        -------
        List[str]
            List of arxiv paper IDs
        """
        return [[i, f.title] for i, f in enumerate(self.papers_dict.values())]

    def get_paper_authors(self) -> List[str]:
        """The function returns the list of Arxiv paper authors that are present
        in the cache

        Returns
        -------
        List[str]
            List of arxiv paper authors
        """
        authors_all = [[i, f.authors] for i, f in enumerate(self.papers_dict.values())]
        return authors_all

    def get_paper_abstracts(self) -> List[str]:
        """The function returns the list of Arxiv paper abstracts that are present
        in the cache

        Returns
        -------
        List[str]
            List of arxiv paper abstracts
        """
        abstract_all = [
            [i, f.abstract] for i, f in enumerate(self.papers_dict.values())
        ]
        return abstract_all

    def get_primary_category(self) -> List[List[str]]:
        all_primary = [[i, f.primary_category] for i, f in enumerate(self.papers_dict.values())]
        return all_primary
    
    def get_secondary_category(self) -> List[List[str]]:
        all_secondary = [[i, f.secondary_category] for i, f in enumerate(self.papers_dict.values())]
        return all_secondary

    def update_paper_list(self, paper: ArxivPaper) -> None:
        """The function updates the cache list self.papers by appending the
        result from the API request into the list

        Parameters
        ----------
        paper_dict : ArxivPaper
            Dictionary representing the results from the Arxiv API request
        """
        paper_id = paper.arxiv_id
        self.papers_dict[paper_id] = paper

    def construct_arxiv_link(
        self,
        paper_title: Union[str, None] = None,
        author: Union[str, None] = None,
        abstract: Union[str, None] = None,
        start_idx: int = 0,
        max_results: int = 100,
    ) -> str:
        """The function that constructs Arxiv link to request the Arxiv API

        Parameters
        ----------
        paper_title : Union[str, None], optional
            Title of the paper as requested by the user, by default None
        author : Union[str, None], optional
            Author of the paper as requested by the user, by default None
        abstract : Union[str, None], optional
            A keyword from Abstract of the paper as requested by the user, by
            default None
        start_idx : int, optional
            Start index for pagination, by default 0
        max_results : int, optional
            End index of the pagination, by default 100

        Returns
        -------
        str
            Arxiv link
        """
        param_dict = {
            "ti": paper_title,
            "au": author,
            "abs": abstract,
        }
        str_query = ""
        query_list = []
        for k, v in param_dict.items():
            if v is not None:
                value_str = " ".join(v.split(" "))
                value_str = f"%22{value_str}%22"
                query_list.append(f"{k}:{value_str}")
        str_query = "+AND+".join(query_list)
        str_query = urllib.parse.quote_plus(str_query)

        str_query += f"&sortBy=relevance&sortOrder=descending&start={start_idx}&max_results={max_results}"
        return ARXIV_LINK + str_query

    def request_arxiv_api_and_update(
        self,
        paper_title: Union[str, None],
        author: Union[str, None],
        abstract: Union[str, None],
    ) -> None:
        """The function requests the Arxiv API and update the list self.papers
        to append the latest cache of papers

        Parameters
        ----------
        paper_title : Union[str, None]
            Title of the paper as requested by the user
        author : Union[str, None]
            Author of the paper as requested by the user
        abstract : Union[str, None]
            A keyword from Abstract of the paper as requested by the user
        """
        # Initializing a list ot store the local results for the user session
        self.local_paper_list = []

        # Construct a URL to requet the Arxiv API
        link_arxiv = self.construct_arxiv_link(
            paper_title=paper_title, author=author, abstract=abstract, max_results=100
        )

        # Request the Arxiv API
        response = requests.get(link_arxiv)

        # The response of Arxiv API is an HTML, parsing the HTML using
        # ElementTree
        xmlstring = response.text
        tree = ET.ElementTree(ET.fromstring(xmlstring))
        tree_root = tree.getroot()
        all_papers = tree_root.findall("n:entry", namespaces=NAMESPACE)

        # Iterating over all the papers for the user request
        for paper in all_papers:
            temp_tile = paper.find("n:title", namespaces=NAMESPACE).text

            all_authors = list(paper.findall("n:author", namespaces=NAMESPACE))

            paper_id = paper.find("n:id", namespaces=NAMESPACE).text.replace(
                "http://arxiv.org/", ""
            )
            paper_abstract = paper.find("n:summary", namespaces=NAMESPACE).text.replace(
                "http://arxiv.org/", ""
            )
            categories = paper.findall("n:category", namespaces=NAMESPACE)
            categories = [f.get("term") for f in categories]
            categories = [f.split(".") for f in categories if ((f is not None) and f.split(".")[0] in ["cs", "math", "econ", "math"] )]
            primary_cats = [f[0] for f in categories]

            # import pdb; pdb.set_trace()
            secondary_cats = [f[1] for f in categories]
            paper_abstract = paper_abstract.replace("\n", " ").lstrip().rstrip()
            paper_author_list = []
            for au in all_authors:
                paper_author_list.append(list(au)[0].text)
            paper_details = {
                "arxiv_id": paper_id,
                "authors": paper_author_list,
                "title": temp_tile,
                "abstract": paper_abstract,
                "primary_category": primary_cats,
                "secondary_category": secondary_cats
            }
            # Update the cache of arxiv papers
            paper = ArxivPaper(**paper_details)
            paper.update_semsch_id()
            self.local_paper_list.append(paper)
            self.update_paper_list(paper)

    def gather_data(
        self, paper_title=None, author=None, abstract=None, use_cache=False, 
        primary_category = None, secondary_category=None
    ) -> List[Dict]:
        """The function that controls the construction of Arxiv papers tree. Note
        that this is not technically a tree but a List. We use this list as
        a seed to construct the SemSchTree and AuthorTree

        Parameters
        ----------
        paper_title : _type_, optional
            The title of the paper as requested by the user, by default None
        author : _type_, optional
            The author of the paper as requested by the user, by default None
        abstract : _type_, optional
            The keyword from abstract of the paper as requested by the user, by
            default None
        use_cache : bool, optional
            A bool to use cached arxiv data or not, by default False

        Returns
        -------
        List[Dict]
            A list of Arxiv papers representing the paper details
        """
        # Transforming inputs from HTML forms
        if paper_title == "":
            paper_title = None
        if author == "":
            author = None
        if abstract == "":
            abstract = None
        if primary_category == "":
            primary_category = None
        if secondary_category == "":
            secondary_category = None

        if ((primary_category is None) and (secondary_category is None)):


            # Extracting cached Titles, authors, and abstracts
            paper_list = self.get_paper_titles()
            author_list = self.get_paper_authors()
            abstract_list = self.get_paper_abstracts()

            if paper_title is not None:
                paper_ids_title = [
                    f[0] for f in paper_list if utils.lev_dist(f[1], paper_title) < 30
                ]
            else:
                paper_ids_title = []
            if author is not None:
                paper_ids_author = [
                    f[0] for f in author_list if utils.arxiv_author_match(author, f[1])
                ]
            else:
                paper_ids_author = []
            if abstract is not None:
                paper_ids_abstract = [
                    f[0]
                    for f in abstract_list
                    if utils.arxiv_abstract_match(f[1], abstract)
                ]
            else:
                paper_ids_abstract = []
            paper_ids = paper_ids_title + paper_ids_author + paper_ids_abstract
            # if the use_cache is True, then use the existung paper titles, abstract,
            # and authors
            if bool(paper_ids) and use_cache == True:
                candidate_papers = [vars(f) for f in self.papers_dict.values()]
                papers_data = np.array(candidate_papers)[paper_ids].tolist()
            else:
                self.request_arxiv_api_and_update(paper_title, author, abstract)
                self.write_cache()
                papers_data = [vars(f) for f in self.local_paper_list]
        else:
            
            candidate_papers = [vars(f) for f in self.papers_dict.values()]
            
            primary_category_list = self.get_primary_category()
            secondary_category_list = self.get_secondary_category()

            if primary_category is not None:
                paperd_ids_primary = [f[0] for f in primary_category_list if primary_category in f[1]]
            else:
                paperd_ids_primary = []
            
            if secondary_category is not None:
                paperd_ids_secondary = [f[0] for f in secondary_category_list if secondary_category in f[1]]
            else:
                paperd_ids_secondary = []
            paper_ids = paperd_ids_secondary + paperd_ids_primary
            paper_ids = list(set(paper_ids))
            papers_data = np.array(candidate_papers)[paper_ids].tolist()            
        return papers_data


class AuthorTree:
    def __init__(self, cache_pth: str):
        self.cache_pth = cache_pth
        self.author_dict = {}
        self.read_cache()

    def read_cache(self):
        """A function that reads the cache from the given input path JSON. It
        appends the result in the dictionary self.authors_dict. Note that this
        function reads a JSON that consists of authors from semantic scholar API
        """
        try:
            with open(self.cache_pth, "r") as f:
                data = json.load(f)
            if bool(data):
                for k, v in data.items():
                    self.author_dict[k] = Authors(**v)
        except:
            pass

    def write_cache(self):
        """The function writes cache for authors from semantic scholar API. It
        takes the dictionary self.author_dict and writes down each author with
        a given ID

        Returns
        -------
        bool
            Returns True if the data is successfully written to the disk, False
            otherwise
        """
        data_save = {}
        try:
            for author_id, val in self.author_dict.items():
                temp_dict = vars(val)
                data_save[author_id] = temp_dict

            with open(self.cache_pth, "w") as f:
                json.dump(data_save, f)
            return True
        except:
            return False

    def get_author_list(self) -> List[str]:
        """A function that returns a list of Author IDs present in the cache

        Returns
        -------
        List[str]
            List of Author IDs
        """
        return list(self.author_dict.keys())

    def request_and_update(self, author_id: str) -> str:
        """A function that updates the dictionary self.author_dict by first
        requesting the semantic scholar API for the author details and then
        appending the author details inside the dict.

        Parameters
        ----------
        author_id : str
            Semantic Scholar Author ID

        Returns
        -------
        str
            The semantic scholar author ID
        """
        author_list = self.get_author_list()
        if author_id in author_list:

            pass
        else:
            papers_req = "papers.title,papers.authors"
            req_fields = f"name,affiliations,homepage,paperCount,citationCount,hIndex,{papers_req}"
            author_url = f"{SEMSCH_LINK}/author/{author_id}?fields={req_fields}"
            _results = requests.get(
                author_url, headers={"x-api-key": SemanticScholarCreds.API_KEY}
            )
            results = _results.json()
            try:
                self.update_author_info(results)
            except:
                import pdb

                pdb.set_trace()

        return author_id

    def update_author_info(self, results: Dict):
        """The function that updates the self.author_dict by appending the
        author detatils retreived from semantic scholar API

        Parameters
        ----------
        results : Dict
            A dictionary that consists of results of a single Author from
            semantic scholar API
        """
        _author_dict = {}

        author_id = results["authorId"]

        _author_dict["id"] = author_id
        _author_dict["name"] = results["name"]
        _author_dict["homepage"] = results["homepage"]
        _author_dict["paper_count"] = results["paperCount"]
        _author_dict["citations"] = results["citationCount"]
        _author_dict["hindex"] = results["hIndex"]

        author_papers = results["papers"]
        author_papers_id = [f["paperId"] for f in author_papers]
        _author_dict["papers"] = author_papers_id

        id_worked_with = [[f["authorId"] for f in f["authors"]] for f in author_papers]
        id_worked_with = [f for ff in id_worked_with for f in ff]

        id_worked_with = list(set(id_worked_with))
        id_worked_with = [f for f in id_worked_with if f != author_id]
        _author_dict["worked_with"] = id_worked_with
        author = Authors(**_author_dict)
        # appending the results inside the dict
        self.author_dict[author_id] = author

    def get_author_data(
        self, SEMSCHTREE: SemSchTree, author_id: str
    ) -> Tuple[str, str, str, str, str, List[Dict], List[Dict]]:
        """The function that returns the author details from the semantic scholar
        API. It returns author.name, author.homepage, author.paper_count,
        author.citation_count, author.hindex, author.worked_with, author.papers_author

        Parameters
        ----------
        SEMSCHTREE : SemSchTree
            A class object of type SemSchTree
        author_id : str
            Author ID that user wants to see more info for

        Returns
        -------
        Tuple[str, str, str, str, str, List[Dict], List[Dict]]
            _description_
        """

        # Requesting results from semantic scholar API for the requested author
        sem_sch_id = self.request_and_update(author_id)
        author = self.author_dict[sem_sch_id]

        # Retreiving the ID of papers that the author wrote
        author_papers_id = author.papers
        author_papers_id = [f for f in author_papers_id if f is not None]

        # Retreiving the ID of authors that the author worked with
        id_worked = author.worked_with
        id_worked = [f for f in id_worked if f is not None]

        # Updating the info for author papers and author IDs if they are not
        # already in the cache
        i = 1
        for a_id in id_worked:
            if self.author_dict.get(a_id):
                pass
            else:
                self.request_and_update(a_id)
                i = i + 1
                if i % 98 == 0:
                    time.sleep(1)
        i = 1
        for p_id in author_papers_id:
            if SEMSCHTREE.papers_dict.get(p_id):
                pass
            else:
                SEMSCHTREE.update_paper_data(p_id)
                i = i + 1
                if i % 98 == 0:
                    time.sleep(1)

        worked_with_id = [f for f in author.worked_with]
        worked_with_authors = [self.author_dict.get(f) for f in worked_with_id]
        worked_with_authors = [f for f in worked_with_authors if f is not None]
        worked_with_authors = [
            f for f in worked_with_authors if f.citations is not None
        ]
        worked_with_authors = sorted(
            worked_with_authors, key=lambda x: x.citations, reverse=True
        )
        # Picking top 50 authors based on the citation count
        worked_with_authors = worked_with_authors[:50]
        worked_with_authors = [vars(f) for f in worked_with_authors]

        # Picking all the authors the author has worked with
        papers_author = [SEMSCHTREE.papers_dict.get(f) for f in author_papers_id]
        papers_author = [f for f in papers_author if f is not None]
        papers_author = [f for f in papers_author if f.citation_count is not None]
        papers_author = sorted(
            papers_author, key=lambda x: x.citation_count, reverse=True
        )
        papers_author = [vars(f) for f in papers_author]

        hindex = author.hindex
        cit_cnt = author.citations
        p_cnt = author.paper_count
        home = author.homepage
        name = author.name

        # Updating the paper ajd author cache
        SEMSCHTREE.write_cache()
        self.write_cache()

        return (name, home, p_cnt, cit_cnt, hindex, worked_with_authors, papers_author)
