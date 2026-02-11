"""
Service État Civil - Ministère de l'Intérieur (Mock)
Port: 8001
Rôle SOA: Vérification de l'existence physique des citoyens
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(
    title="Service État Civil - Ministère de l'Intérieur",
    description="API de vérification de l'existence physique (Loi 83-12, Article 6)",
    version="1.0-Mock"
)


class CitizenStatus(BaseModel):
    """Contrat de service (Service Contract)"""
    nss: str
    en_vie: bool
    date_deces: Optional[str] = None
    lieu_naissance: Optional[str] = None


@app.get("/health")
def health_check():
    return {
        "service": "État Civil",
        "status": "healthy",
        "ministere": "Intérieur et Collectivités Locales",
        "version": "1.0-Mock"
    }


@app.get("/verify/{nss}", response_model=CitizenStatus)
def verifier_existence(nss: str):
    """
    Endpoint SOA: Vérification de l'existence d'un citoyen

    Logique Mock:
    - NSS se terminant par "00" → Décédé (pour tests)
    - Autres NSS → Vivant

    En production, cet endpoint interrogerait la vraie base État Civil
    avec des registres de naissance/décès.
    """
    print(f"[État Civil] Requête reçue pour NSS: {nss}")

    # Simulation: NSS finissant par "00" = Décédé
    if nss.endswith("00"):
        return CitizenStatus(
            nss=nss,
            en_vie=False,
            date_deces=datetime.now().isoformat(),
            lieu_naissance="Alger (Mock)"
        )

    # Tous les autres cas: Vivant
    return CitizenStatus(
        nss=nss,
        en_vie=True,
        date_deces=None,
        lieu_naissance="Alger (Mock)"
    )


@app.get("/")
def root():
    return {
        "message": "Service État Civil - API Ready",
        "documentation": "/docs",
        "endpoint_principal": "/verify/{nss}"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)