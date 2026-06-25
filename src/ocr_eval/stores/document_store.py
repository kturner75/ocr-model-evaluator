import yaml
from ocr_eval.config import CONFIG_DOCUMENTS_DIR
from ocr_eval.models.domain import Document


def list_documents() -> list[Document]:
    docs = []
    for f in sorted(CONFIG_DOCUMENTS_DIR.glob("*.yaml")):
        with open(f) as fh:
            data = yaml.safe_load(fh)
        docs.append(Document(
            id=data["id"], name=data["name"], file_path=data["file_path"],
            doc_type=data["doc_type"], description=data.get("description", ""),
        ))
    return docs


def get_document(doc_id: str) -> Document | None:
    for doc in list_documents():
        if doc.id == doc_id:
            return doc
    return None
