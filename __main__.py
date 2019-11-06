import click
import piman


@click.group()
def cli():
    pass


@cli.command()
def server():    
    piman.server()


@cli.command()
@click.argument('switch_ports', nargs=-1, type=click.INT)
def restart(switch_ports):
    piman.restart(switch_ports)


@cli.command()
@click.argument('ip')
def reinstall(ip):
    piman.reinstall(ip)

@cli.command()
@click.argument('pi_address')
@click.argument('port_on_localhost')
def remshell(pi_address, port_on_localhost):
    piman.remshell(pi_address, port_on_localhost)

if __name__ == "__main__":
    cli()
