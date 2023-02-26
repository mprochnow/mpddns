from distutils.core import setup

setup(name="mpddns",
      version="0.9.0",
      description="mpddns",
      long_description="A simple service to run your own dynamic DNS",
      author="Martin J. Prochnow",
      author_email="email@martin-prochnow.de",
      url="https://github.com/mprochnow/mpddns",
      license="GNU GPL v3",
      platforms="Linux",
      packages=["mpddns"],
      scripts=["bin/mpddns_server", "bin/mpddns_client"])
