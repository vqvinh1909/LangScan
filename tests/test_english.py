# -*- coding: utf-8 -*-
import pytest


@pytest.mark.parametrize("word, base", [
    ("studying", "study"), ("deploying", "deploy"), ("went", "go"),
    ("children", "child"), ("studies", "study"), ("mice", "mouse"),
])
def test_lemma(en, word, base):
    # Tu goc hien kem trong ngoac: "studying  (study)"
    assert en.card(word).word == "{}  ({})".format(word, base)


@pytest.mark.parametrize("word, ipa", [
    ("went", "/ˈwɛnt/"),             # khong phai /ɡoʊ/ cua 'go'
    ("children", "/ˈtʃɪɫdɹən/"),     # khong phai /tʃaɪld/ cua 'child'
])
def test_ipa_of_inflected_form(en, word, ipa):
    assert en.card(word).reading == ipa


def test_ipa_falls_back_to_base(en):
    # Tu nao khong co IPA rieng thi van phai co phien am (lay cua tu goc)
    assert en.card("deploying").reading


def test_it_term_has_priority(en):
    card = en.card("firewall")
    assert card.badge == "IT"
    assert "tường lửa" in card.vi[0]


def test_it_multiword_phrase(en):
    words = [c.word for c in en.cards("we need a load balancer")]
    assert "load balancer" in words


def test_proper_noun_not_translated(en):
    assert en.card("Zalo").badge == "tên riêng"
