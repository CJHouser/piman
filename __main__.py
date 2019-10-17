import click
import piman
from utility import power_cycle

@click.group()
def cli():
    pass


@cli.command()
def server():    
    piman.server()


@cli.command()
@click.argument('switch_port', type=click.INT)
def restart(switch_port):
    piman.restart(switch_port)


@cli.command()
@click.argument('switch_port', type=click.INT)
def reinstall(switch_port):
    piman.reinstall(switch_port)


if __name__ == "__main__":
    cli()
