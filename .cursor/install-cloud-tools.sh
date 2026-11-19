#!/usr/bin/env bash
set -euo pipefail

cache=${1:?tool cache directory required}
readonly tofu_version=1.13.9
readonly helm_version=v4.3.2
readonly tflint_version=v0.66.0
readonly kubeconform_version=v0.7.0

case "$(uname -m)" in
    x86_64)
        arch=amd64
        tofu_checksum=bc44eb6b06446ba83bd4072114891987f590f66cca712737a7f1147c50c539ce
        helm_checksum=d1c0278d46beab79582d7e50f5b3dc206944ba8e577cde618513fd07daa53983
        tflint_checksum=22be11cadc25cd02401e94c0ccc91aa63467debb8485c2a755d98f4c0a9d1e2e
        kubeconform_checksum=c31518ddd122663b3f3aa874cfe8178cb0988de944f29c74a0b9260920d115d3
        ;;
    aarch64)
        arch=arm64
        tofu_checksum=04f7c93828b859d420269ed30f923ffebf09157b5d7fb95bf8d88a4d208b7fa3
        helm_checksum=df31cb61680ef728f82c770e5280dd565617bee6b039d37e85c677288be4bbb0
        tflint_checksum=1105a0a5ddee7cdac7957a3475571a946b839192ea1bc0c722c6c4686001067e
        kubeconform_checksum=cc907ccf9e3c34523f0f32b69745265e0a6908ca85b92f41931d4537860eb83c
        ;;
    *)
        echo "Unsupported tool architecture: $(uname -m)" >&2
        exit 1
        ;;
esac

mkdir -p "$cache/bin"
scratch="$(mktemp -d "$cache/.download.XXXXXX")"
trap 'rm -rf -- "$scratch"' EXIT

install_tool() {
    local name="$1" url="$2" checksum="$3" member="$4"
    local destination="$cache/releases/$checksum/$name"
    local archive="$scratch/${url##*/}"
    if [[ ! -x "$destination" ]]; then
        curl -q --fail --silent --show-error --location --retry 3 \
            --proto '=https' --proto-redir '=https' --output "$archive" "$url"
        printf '%s  %s\n' "$checksum" "$archive" | sha256sum --check --strict -
        case "$archive" in
            *.zip) unzip -p "$archive" "$member" > "$scratch/$name" ;;
            *.tar.gz) tar -xOzf "$archive" "$member" > "$scratch/$name" ;;
        esac
        chmod 0755 "$scratch/$name"
        mkdir -p "$(dirname "$destination")"
        mv -- "$scratch/$name" "$destination"
    fi
    ln -sfn -- "$destination" "$cache/bin/$name"
}

install_tool tofu \
    "https://github.com/opentofu/opentofu/releases/download/v${tofu_version}/tofu_${tofu_version}_linux_${arch}.zip" \
    "$tofu_checksum" tofu
install_tool helm "https://get.helm.sh/helm-${helm_version}-linux-${arch}.tar.gz" \
    "$helm_checksum" "linux-$arch/helm"
install_tool tflint \
    "https://github.com/terraform-linters/tflint/releases/download/${tflint_version}/tflint_linux_${arch}.zip" \
    "$tflint_checksum" tflint
install_tool kubeconform \
    "https://github.com/yannh/kubeconform/releases/download/${kubeconform_version}/kubeconform-linux-${arch}.tar.gz" \
    "$kubeconform_checksum" kubeconform
