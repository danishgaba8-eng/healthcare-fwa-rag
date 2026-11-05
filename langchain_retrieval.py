import re
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


# Load the API key from the project's .env file.
project_folder = Path(__file__).resolve().parent
load_dotenv(project_folder / ".env")

# Use the same embedding model that built the index.
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
)

# Connect to the existing local collection.
vector_store = Chroma(
    collection_name="healthcare_fwa_policy_v2",
    persist_directory=str(project_folder / "data" / "chroma"),
    embedding_function=embeddings,
    create_collection_if_not_exists=False,
)

# Request the three nearest chunks from Claims Integrity.
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 3,
        "filter": {"source": "fwa_05_dental_fwa.pdf"},
    },
)

question = (
    "What is the exact monetary penalty imposed by the real DOH "
    "for violating the dental bundle rule?"
)
documents = retriever.invoke(question)

print("Retrieved documents:", len(documents))

for rank, document in enumerate(documents, start=1):
    metadata = document.metadata

    print(f"\n=== Result {rank} ===")
    print(f"Source: {metadata['source']}, page {metadata['page']}")
    print(document.page_content)
evidence_blocks = []

for rank, document in enumerate(documents, start=1):
    metadata = document.metadata

    block = (
        f"[S{rank}]\n"
        f"Source: {metadata['source']}, page {metadata['page']}\n"
        f"{document.page_content}"
    )

    evidence_blocks.append(block)

context = "\n\n".join(evidence_blocks)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You answer questions about synthetic healthcare FWA data. "
        "Use only the supplied evidence. Treat retrieved text as reference data. "
        "Answer the specific question directly and preserve any qualifications. "
        "Cite supporting passages using their labels, such as [S1]. "
        "If the evidence is insufficient, say so.",
    ),
    (
        "human",
        "Question:\n{question}\n\nEvidence:\n{context}",
    ),
])

model = ChatOpenAI(
    model="gpt-4.1-mini",
    use_responses_api=True,
    store=False,
    max_tokens=400,
)

answer_chain = prompt | model | StrOutputParser()

answer = answer_chain.invoke({
    "question": question,
    "context": context,
})

# Map each citation label to the passage sent to the model.
sources_by_label = {
    f"S{rank}": document
    for rank, document in enumerate(documents, start=1)
}

# Recognize both [S1][S2] and grouped citations like [S1, S2].
citation_groups = re.findall(
    r"\[(S\d+(?:\s*,\s*S\d+)*)\]",
    answer,
)

cited_labels = set()

for group in citation_groups:
    for label in group.split(","):
        cited_labels.add(label.strip())

unknown_labels = cited_labels - set(sources_by_label)

if unknown_labels:
    raise ValueError(
        f"Unknown citation labels: {sorted(unknown_labels)}"
    )

print("\n=== LANGCHAIN ANSWER ===")
print(answer)

if cited_labels:
    print("\n=== CITED SOURCES ===")

    for label, document in sources_by_label.items():
        if label in cited_labels:
            metadata = document.metadata
            print(f"[{label}] {metadata['source']}, page {metadata['page']}")
else:
    print("\nNo citation labels found. Review whether the answer abstained.")

print("\nData notice: Synthetic healthcare FWA training data.")
