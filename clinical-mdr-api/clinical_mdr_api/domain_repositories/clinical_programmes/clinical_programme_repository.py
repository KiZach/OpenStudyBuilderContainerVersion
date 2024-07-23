from threading import Lock
from typing import Collection

from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from clinical_mdr_api import config
from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,
)
from clinical_mdr_api.domain_repositories.models.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.repositories._utils import sb_clear_cache


class ClinicalProgrammeRepository:
    cache_store_item_by_uid = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )
    lock_store_item_by_uid = Lock()

    def generate_uid(self) -> str:
        return ClinicalProgramme.get_next_free_uid_and_increment_counter()

    def clinical_programme_exists(self, clinical_programme_uid: str) -> bool:
        clinical_programme_node = ClinicalProgramme.nodes.get_or_none(
            uid=clinical_programme_uid
        )
        return bool(clinical_programme_node)

    def get_hashkey(
        self,
        uid: str,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.
        """
        return hashkey(
            str(type(self)),
            uid,
        )

    @cached(cache=cache_store_item_by_uid, key=get_hashkey, lock=lock_store_item_by_uid)
    def find_by_uid(self, uid: str) -> ClinicalProgrammeAR | None:
        clinical_programme = ClinicalProgramme.nodes.get_or_none(uid=uid)
        if clinical_programme is not None:
            clinical_programme = ClinicalProgrammeAR.from_input_values(
                name=clinical_programme.name,
                generate_uid_callback=lambda: clinical_programme.uid,
            )
            return clinical_programme
        return None

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, clinical_programme: ClinicalProgrammeAR) -> None:
        """
        Public repository method for persisting a (possibly modified) state of the Clinical Programme instance into the underlying
        DB. Provided instance can be brand new instance (never persisted before) or an instance which has been
        retrieved with find_by_uid(...).

        :param clinical_programme: an instance of a clinical programme aggregate (ClinicalProgrammeAR class) to persist
        """
        repository_closure_data = clinical_programme.repository_closure_data

        if repository_closure_data is None:
            # if save gets an object without a closure - it's a new object.
            # object should already have a UID.
            clinical_programme = ClinicalProgramme(
                uid=clinical_programme.uid, name=clinical_programme.name
            )
            clinical_programme.save()
        else:
            # if save gets an object with a closure, it's a modified existing object.
            raise NotImplementedError

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def find_all(self) -> Collection[ClinicalProgrammeAR]:
        clinical_programmes: list[ClinicalProgramme] = ClinicalProgramme.nodes.all()
        # projecting results to ClinicalProgrammeAR instances
        clinical_programmes: list[ClinicalProgrammeAR] = [
            ClinicalProgrammeAR.from_input_values(
                name=p.name, generate_uid_callback=lambda p=p: p.uid
            )
            for p in clinical_programmes
        ]

        # attaching a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for clinical_programme in clinical_programmes:
            clinical_programme.repository_closure_data = repository_closure_data

        return clinical_programmes
