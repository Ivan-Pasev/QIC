from qic.core import ConstitutionSnapshot, Maturity, PRIME_LAWS


def test_constitution_snapshot_contains_all_prime_laws() -> None:
    snapshot = ConstitutionSnapshot()
    assert snapshot.prime_laws == PRIME_LAWS
    assert len(snapshot.prime_laws) >= 8


def test_constitution_snapshot_is_immutable() -> None:
    snapshot = ConstitutionSnapshot()
    try:
        snapshot.version = "mutated"  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError("constitutional snapshot must be immutable")


def test_maturity_labels_are_non_cumulative() -> None:
    assert Maturity.IMPLEMENTED.supports(Maturity.IMPLEMENTED)
    assert not Maturity.IMPLEMENTED.supports(Maturity.TESTED)
    assert not Maturity.SIMULATED.supports(Maturity.FORMALLY_MODELED)
    assert not Maturity.FORMALLY_MODELED.supports(Maturity.SIMULATED)


def test_prime_boundary_laws_are_present() -> None:
    required = {
        "Generation != Authority",
        "Proposal != Canonical Knowledge",
        "Remote State != Local Authority",
        "Decision != Physical Actuation",
    }
    assert required.issubset(set(PRIME_LAWS))
