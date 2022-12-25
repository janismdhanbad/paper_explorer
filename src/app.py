import json

import pandas as pd
from flask import Flask, render_template, request

from generate_object_tree import ArxivTree, AuthorTree, SemSchTree

CACHE_ARXIV = "../data/papers_arxiv_v1.json"
CACHE_SEMSCH = "../data/papers_semsch_v1.json"
CACHE_AUTHORS = "../data/authors_semsch_v1.json"
ARXIVTREE = ArxivTree(CACHE_ARXIV)
SEMSCHTREE = SemSchTree(CACHE_SEMSCH)
AUTHORTREE = AuthorTree(CACHE_AUTHORS)

app = Flask(__name__)


@app.route("/")
def index():
    """Main landing page"""

    return render_template("index.html")


@app.route("/papers", methods=["GET", "POST"])
def paper_display():
    """The function displays the paper results after the first user input using
    HTML form

    Returns
    -------
    HTML
        A renderable HTML that is shown to the user
    """
    # Extracting user inputs
    paper_title = request.form["paper_title"]
    author_name = request.form["author_name"]
    keyword = request.form["keyword"]
    primary_cat = request.form["primary_cat"]
    secondary_cat = request.form["secondary_cat"]
    # import pdb; pdb.set_trace()
    # Checking if the user checked using cache
    if request.form.get("use_cache"):
        use_cache = True
    else:
        use_cache = False
    # Retreiving paper data based on user inputs
    paper_results = ARXIVTREE.gather_data(
        paper_title=paper_title,
        author=author_name,
        abstract=keyword,
        use_cache=use_cache,
        primary_category=primary_cat,
        secondary_category =secondary_cat
    )
    return render_template("papers.html", paper_results=paper_results)


@app.route("/papers/paper_explore", methods=["GET", "POST"])
def explore_paper():
    """The function reeturns an HTML page that shows all the details about the
    paper, i.e., its authors, its references and its citations. Note that the
    paper_id here is the Arxiv paper ID and NOT the semantic scholar paper ID

    Returns
    -------
    html
        A renderable HTML that contains results for paper selected by the user.
    """
    if request.form.get("paper_id"):
        # Extracting Arxiv paper ID
        arxiv_id_paper = request.form["paper_id"]
        semsch_id = ARXIVTREE.papers_dict[arxiv_id_paper].id
        # primary_category = ARXIVTREE.papers_dict[arxiv_id_paper].primary_category
        # secondary_category = ARXIVTREE.papers_dict[arxiv_id_paper].secondary_category

        (
            title,
            authors,
            abstract,
            ref_cnt,
            cit_cnt,
            inf_cit,
            url,
            reference_list,
            citation_list,
        ) = SEMSCHTREE.fetch_paper_data(semsch_id)
        return render_template(
            "paper_explore.html",
            title=title,
            authors=authors,
            abstract=abstract,
            ref_cnt=ref_cnt,
            cit_cnt=cit_cnt,
            inf_cit=inf_cit,
            url=url,
            reference_list=reference_list,
            citation_list=citation_list,
        )


@app.route("/papers/paper_explore_sch", methods=["GET", "POST"])
def explore_paper_sch():
    """The function reeturns an HTML page that shows all the details about the
    paper, i.e., its authors, its references and its citations. Note that the
    paper_id here is the semantic scholar paper ID and NOT the Arxiv paper ID

    Returns
    -------
    html
        A renderable HTML that contains results for paper selected by the user.
    """
    if request.form.get("paper_id"):
        id_paper = request.form["paper_id"]
        (
            title,
            authors,
            abstract,
            ref_cnt,
            cit_cnt,
            inf_cit,
            url,
            reference_list,
            citation_list,
        ) = SEMSCHTREE.fetch_paper_data(id_paper)
        return render_template(
            "paper_explore.html",
            title=title,
            authors=authors,
            abstract=abstract,
            ref_cnt=ref_cnt,
            cit_cnt=cit_cnt,
            inf_cit=inf_cit,
            url=url,
            reference_list=reference_list,
            citation_list=citation_list,
        )


@app.route("/papers/author_explore", methods=["GET", "POST"])
def explore_author_sch():
    """The fuunction returns a renderable HTML for the author ID selected by the
    user. The details here consist of Author's papers and other authors that the
    author has worked with.

    Returns
    -------
    html
        A renderable HTML that contains results for author selected by the user.
    """
    # Extracting the author ID
    if request.form.get("author_id"):
        author_id = request.form["author_id"]
        (
            name,
            home,
            p_cnt,
            cit_cnt,
            hindex,
            worked_with_authors,
            papers_author,
        ) = AUTHORTREE.get_author_data(SEMSCHTREE, author_id)
        return render_template(
            "author_explore.html",
            name=name,
            home=home,
            p_cnt=p_cnt,
            cit_cnt=cit_cnt,
            hindex=hindex,
            worked_with_authors=worked_with_authors,
            papers_author=papers_author,
        )


@app.route("/prev_searches", methods=["GET", "POST"])
def prev_papers_explored():
    """The function returns the previous papers explored by the user

    Returns
    -------
    html
        A renderable HTML page that contains information about user's previous
        searches
    """
    df = pd.read_csv("../data/prev_searches.csv")
    df_records = df.to_dict("records")
    return render_template("prev_searches.html", records=df_records)


@app.route("/paper_corpus", methods=["GET", "POST"])
def paper_corpus_explored():
    """The function returns a renderable HTML that contains papers in the
    corpus(cached file). Note that it might be possible that a paper is present
    in the corpus(cache file) and still takes time to load. This is because
    we need to request the sematic scholar API for the details about a paper's
    authors, references and citations.

    Returns
    -------
    html
        A renderable HTML page that contains information about papers in the
        corpus
    """
    req_keys = [
        "id",
        "title",
        "reference_count",
        "citation_count",
        "influential_paper_citations",
    ]
    with open(CACHE_SEMSCH, "r") as f:
        data_paper = json.load(f)

    paper_records = data_paper.values()
    paper_records = [
        {k: v for k, v in f.items() if k in req_keys} for f in paper_records
    ]

    return render_template("paper_corpus.html", paper_records=paper_records)


@app.route("/author_corpus", methods=["GET", "POST"])
def author_corpus_explored():
    """The function returns a renderable HTML that contains papers in the
    corpus(cached file). Note that it might be possible that an author is present
    in the corpus(cache file) and still takes time to load. This is because
    we need to request the sematic scholar API for the details about a author's
    papers and the other authors who worked with the author.

    Returns
    -------
    html
        A renderable HTML page that contains information about authors in the
        corpus
    """
    req_keys = ["id", "name", "paper_count", "citations", "hindex"]
    with open(CACHE_AUTHORS, "r") as f:
        data_authors = json.load(f)

    author_records = data_authors.values()
    author_records = [
        {k: v for k, v in f.items() if k in req_keys} for f in author_records
    ]

    return render_template("author_corpus.html", author_records=author_records)


if __name__ == "__main__":
    print("starting Flask app", app.name)
    app.run(debug=True)
