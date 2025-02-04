import numpy as np
import ovito


class LatticeGenerator:
    def load_np(lattice: np.ndarray):
        """
        Initialize a generator with a given lattice; use OVITO for analysis
        - lattice: expects a numpy array (n x 3) of perfect lattice positions
        """
        self.lattice = ovito.DataCollection()
        self.lattice.particles_.create_property("Position", data=lattice)
        self.calculate_nn_distance()

    def load_ovito(lattice: ovito.data.DataCollection):
        """
        Initialize a generator with a given lattice; use OVITO for analysis
        - lattice: expects a DataCollection object of perfect lattice positions
        """
        self.lattice = lattice
        self.calculate_nn_distance()

    def load_lammps(filename: str):
        """
        Initialize a generator with a given lattice; use OVITO for analysis
        - filename: expects a string of the path to a LAMMPS data file
        """
        pipeline = ovito.io.import_file(filename)
        self.lattice = pipeline.compute()
        self.calculate_nn_distance()

    def calculate_nn_distance(self):
        """
        Calculate the nearest neighbor distance of the initialized lattice using OVITO.
        Loads from internal lattice. NearestNeighborFinder is a generator which results
        in mildly strange syntax in this use case
        """
        self.nn_distance = next(
            ovito.data.NearestNeighborFinder(1, self.lattice).find(0)
        ).distance

    def generate(self, alpha):
        """
        Generate a synthetic sample of initialized lattice with a given thermal alpha.
        - alpha: percentage of nearest neighbor distance to displace atoms
        """
        displaced_lattice = self.lattice.clone()
        displacement_radius = alpha * self.nn_distance
        n_atoms = self.lattice.particles.count

        # generate random displacements
        # https://stackoverflow.com/questions/5408276/sampling-uniformly-distributed-random-points-inside-a-spherical-volume
        # we could potentially speed this up by sampling from a cube and rejecting points outside the sphere
        phi = np.random.uniform(0, 2 * np.pi, n_atoms)
        theta = np.random.uniform(0, np.pi, n_atoms)
        r = np.cbrt(np.random.uniform(0, displacement_radius, n_atoms))

        # apply displacements
        displaced_lattice.particles_.positions_[:] += np.array(
            [
                r * np.sin(theta) * np.cos(phi),
                r * np.sin(theta) * np.sin(phi),
                r * np.cos(theta),
            ]
        ).T

        return displaced_lattice

    def generate_range(self, alpha_min, alpha_max, n):
        """
        Generate a range of synthetic samples of initialized lattice with thermal alphas
        ranging from alpha_min to alpha_max.
        """
        alphas = np.linspace(alpha_min, alpha_max, n)
        return [self.generate(alpha) for alpha in alphas]

    def save(self, path, displaced_lattice):
        """
        Save the generated samples to a LAMMPS data file. (Probably shouldn't be used in practice)
        """
        ovito.io.export_file(
            displaced_lattice,
            path,
            columns=[
                "Particle Identifier",
                "Particle Type",
                "Position.X",
                "Position.Y",
                "Position.Z",
            ],
        )
