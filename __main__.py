import click
import piman
from utility import power_cycle

@click.group()
def cli():
    pass


#@cli.command()
#def server    piman.server()


@cli.command()
@click.argument('id')
def restart(id):
    piman.restart(id)


@cli.command()
@click.argument('id')
def reinstall(id):
    piman.reinstall(id)

@cli.command()
def power_cycle():
    piman.power_cycle(10)
    #server()

if __name__ == "__main__":
    cli()
