import json
import zipfile


def sample():
    return {"v": "5.12.2", "fr": 30, "ip": 0, "op": 60, "w": 100, "h": 100, "layers": [], "assets": []}


def test_discovers_new_downloads_and_skips_partial_files(tmp_path):
    from app.animations import discover

    assert discover(tmp_path) == {}
    path = tmp_path / "jio-wifi-animation_10697936.json"
    path.write_text('{"v":')
    assert discover(tmp_path) == {}
    path.write_text(json.dumps(sample()))
    assert discover(tmp_path)["Jio"]["w"] == 100
    (tmp_path / "vi-network-animation_11625736.json").write_text(json.dumps(sample()))
    assert set(discover(tmp_path)) == {"Jio", "Vi"}


def test_dotlottie_embeds_packaged_images_without_extracting_files(tmp_path):
    from app.animations import discover

    animation = sample()
    animation["assets"] = [{"id": "image_0", "u": "", "p": "images/icon.png"}]
    with zipfile.ZipFile(tmp_path / "bsnl-sim-card-animation_10437298.lottie", "w") as archive:
        archive.writestr("manifest.json", json.dumps({"animations": [{"id": "main"}]}))
        archive.writestr("animations/main.json", json.dumps(animation))
        archive.writestr("images/icon.png", b"sample-image")
    asset = discover(tmp_path)["BSNL"]["assets"][0]
    assert asset["p"].startswith("data:image/png;base64,")
    assert asset["e"] == 1
    assert not (tmp_path / "images").exists()


def test_discovers_supplied_video_previews_and_detects_actual_format(tmp_path):
    from app.animations import discover

    folder = tmp_path / "assets" / "animations"
    folder.mkdir(parents=True)
    (folder / "jio_wi_fi_animation_10697936.mp4").write_bytes(b"\x1aE\xdf\xa3" + b"webm-preview" * 20)
    frame = discover(tmp_path)["Jio"]
    assert frame["media"]["src"].startswith("data:video/webm;base64,")
