import setuptools

setuptools.setup(
    name="horus_deploy",
    version="0.2.0",
    author="Horus View and Explore B.V.",
    author_email="info@horus.nu",
    description="Configuration deployment for Horus devices.",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=[
        "horus_deploy",
        "horus_deploy.builtin_deploy_scripts",
        "horus_deploy.operations",
    ],
    package_data={
        "": ["default_id_ed25519", "default_id_ed25519.pub"],
    },
    python_requires=">=3.8",
    install_requires=[
        "click",
        "pyinfra",
        "tabulate",
        "zeroconf",
    ],
    entry_points={
        "console_scripts": ["horus-deploy=horus_deploy.cli:main"],
    },
)
