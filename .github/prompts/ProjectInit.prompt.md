---
mode: agent
---
# Iniciar un nuevo proyecto de Python con CI/CD y estructura recomendada

Eres un asistente experto en desarrollo de software y DevOps. Tu tarea es ayudar a crear la estructura inicial de un nuevo proyecto de Python que incluya integración continua (CI) y despliegue continuo (CD) utilizando GitHub Actions.

Debes de tener en cuenta que ProjectName es un marcador de posición para el nombre real del proyecto, que debe ser reemplazado por el nombre proporcionado por el usuario.

Crear un la estructura de directorio similar a la siguiente, asegurándote de incluir los archivos y carpetas necesarios para un proyecto de Python bien organizado con CI/CD:

```ProjectName

/
├── .vscode/
│   └── settings.json
├── .github/
│   ├── prompts/
│   ├── workflows/
│   │   └── release-auto.yml
│   │   └── test-and-deploy.yml
│   ├── config/
│   │   ├── .gitattributes
│   │   ├── .gitignore
├── hooks/
│   ├── .gitkeep
│   ├── create_git_tag_from_changelog.py
├── resources/
│   ├── docs/
│   │   ├── CHANGELOG.md
│   │   ├── srs.md
│   │   ├── srvp.md
│   ├── images/
│   │   ├── image1.png
│   │   ├── image2.png
│   ├── .codeviz/
│   │   ├── app-diagram.drawio
│   │   ├── app-diagram.png
│   ├── .gitkeep
│   ├── requirements.txt
│   ├── version_info.txt
│   ├── ProjectName.toml
│   ├── ProjectName.spec
├── setup.py
├── logs/
├── tests/
│   ├── .gitkeep
│   ├── conftest.py
│   ├── test_main.py
├── scripts/
│   ├── .gitkeep
│   ├── build.sh
│   ├── build.ps1
│   ├── install.sh
│   ├── install.ps1
│   ├── test.sh
│   ├── test.ps1
├── core/
│   ├── .gitkeep
│   ├── __init__.py
│   ├── gui.py
│   ├── main.py
│   ├── utils.py
│   ├── version.py
│   ├── version.txt
├── setup.py
├── ProjectName.py
└── README.md

```

Asegúrate de que los archivos de configuración de GitHub Actions en `.github/workflows/` estén configurados para ejecutar pruebas, crear versiones y desplegar a entornos de staging y producción. Incluye scripts básicos en la carpeta `scripts/` para construir, instalar y probar el proyecto.

Proporciona contenido inicial para los archivos clave como `setup.py`, `requirements.txt`, y los archivos de workflow de GitHub Actions. Asegúrate de que el proyecto siga las mejores prácticas de desarrollo de software y DevOps.
