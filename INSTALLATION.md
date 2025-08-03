### Installing Both Ollama and Open WebUI Using Kustomize

For cpu-only pod

```bash
kubectl apply -f ./kubernetes/manifest/base
```

For gpu-enabled pod

```bash
kubectl apply -k ./kubernetes/manifest
```

### Installing Both Ollama and Open WebUI Using Helm

Package Helm file first

```bash
helm package ./kubernetes/helm/
```

For cpu-only pod

```bash
helm install ollama-webui ./ollama-webui-*.tgz
```

For gpu-enabled pod

```bash
helm install ollama-webui ./ollama-webui-*.tgz --set ollama.resources.limits.nvidia.com/gpu="1"
```

Check the `kubernetes/helm/values.yaml` file to know which parameters are available for customization
### Installing Cuda Drivers

```bash
 dnf clean all
 dnf -y install libcudnn8 libcudnn8-devel
```

### Environment Variables

- `GUNICORN_TIMEOUT`: Gunicorn worker timeout in seconds (default: `120`).
- `TTS_ENGINE`: Text-to-speech engine. Use `TTS_ENGINE=whisperspeech` to enable WhisperSpeech and install its extras (`webdataset`, `fastcore`, `fastprogress`, `torchaudio`, `speechbrain`, `vocos`).
