
__all__ = ["ALLATOM", "POLYALA", "RELIABLE", "SIDE_CHAIN_TREATMENTS", 
           "UNMODIFIED", "THIN_CLUSTERS"]

# Module-level definitions. These need to come here because they are used in ample_util, which we also import
# If they are defined after ample_util is imported then they aren't seen by ample_util and we get an import error
POLYALA = 'polyAla'
RELIABLE = 'reliable'
ALLATOM = 'allatom'
UNMODIFIED = 'unmod'
SIDE_CHAIN_TREATMENTS = [POLYALA, RELIABLE, ALLATOM]
THIN_CLUSTERS = False