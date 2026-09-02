#!/usr/bin/env bash
# ==============================================================================
# Generate SAML SP Certificate and Metadata XML
# Run on the host where Elasticsearch / Kibana runs.
# ==============================================================================
set -euo pipefail

OUT_DIR="${1:-./saml-certs}"
mkdir -p "$OUT_DIR"

echo "[+] Generating SP private key (RSA 2048)..."
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$OUT_DIR/sp-key.pem"

echo "[+] Generating SP certificate (valid 10 years)..."
openssl req -new -x509 -key "$OUT_DIR/sp-key.pem" -days 3650 \
  -out "$OUT_DIR/sp-cert.pem" \
  -subj "/CN=elastic-saml-sp" \
  -addext "subjectAltName=DNS:localhost"

echo "[+] Building PKCS#12 keystore for Elasticsearch..."
openssl pkcs12 -export \
  -in "$OUT_DIR/sp-cert.pem" \
  -inkey "$OUT_DIR/sp-key.pem" \
  -out "$OUT_DIR/saml-sp-keystore.p12" \
  -passout pass:changeme-sp-key-password

echo "[+] Building PKCS#12 keystore for Kibana..."
openssl pkcs12 -export \
  -in "$OUT_DIR/sp-cert.pem" \
  -inkey "$OUT_DIR/sp-key.pem" \
  -out "$OUT_DIR/kibana-saml-keystore.p12" \
  -passout pass:changeme-kibana-sp-password

echo "[+] Generating SP metadata XML (upload to IdP)..."
# Build certificate block (strip PEM headers/footers, join lines)
CERT_B64=$(openssl x509 -in "$OUT_DIR/sp-cert.pem" -outform DER | openssl base64 -A)

cat > "$OUT_DIR/sp-metadata.xml" <<XMLEOF
<?xml version="1.0" encoding="UTF-8"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  entityID="http://localhost:9200">
  <SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing">
      <KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
        <X509Data>
          <X509Certificate>${CERT_B64}</X509Certificate>
        </X509Data>
      </KeyInfo>
    </KeyDescriptor>
    <AssertionConsumerService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="http://localhost:9200/saml/acs"
      index="0" />
  </SPSSODescriptor>
</EntityDescriptor>
XMLEOF

echo ""
echo "=== SP Certificate Files ==="
ls -la "$OUT_DIR/"

echo ""
echo "=== Next Steps ==="
echo "1. Upload sp-metadata.xml to your IdP as a trusted SP."
2. Download IdP metadata XML and save as idp-metadata.xml
3. Copy .p12 files to /etc/elasticsearch/saml/ and /etc/kibana/saml/.
4. Merge elasticsearch-saml.yml into elasticsearch.yml.
5. Merge kibana-saml.yml into kibana.yml.
6. Restart Elasticsearch then Kibana.
