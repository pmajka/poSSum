ITK_COORDINATE_UNKNOWN = 0
ITK_COORDINATE_Right = 2
ITK_COORDINATE_Left = 3
ITK_COORDINATE_Posterior = 4
ITK_COORDINATE_Anterior = 5
ITK_COORDINATE_Inferior = 8
ITK_COORDINATE_Superior = 9

ITK_COORDINATE_PrimaryMinor = 0
ITK_COORDINATE_SecondaryMinor = 8
ITK_COORDINATE_TertiaryMinor = 16

ITK_COORDINATE_ORIENTATION_INVALID = ITK_COORDINATE_UNKNOWN,

ITK_COORDINATE_ORIENTATION_RIP = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_LIP = ( ITK_COORDINATE_Left << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_RSP = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_LSP = ( ITK_COORDINATE_Left << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_RIA = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_LIA = ( ITK_COORDINATE_Left << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_RSA = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_LSA = ( ITK_COORDINATE_Left << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )



ITK_COORDINATE_ORIENTATION_IRP = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ILP = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SRP = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SLP = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_IRA = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ILA = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SRA = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SLA = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_TertiaryMinor )


ITK_COORDINATE_ORIENTATION_RPI = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_LPI = ( ITK_COORDINATE_Left << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_RAI = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )
ITK_COORDINATE_ORIENTATION_LAI = ( ITK_COORDINATE_Left
                                    << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_RPS = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_LPS = ( ITK_COORDINATE_Left << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_RAS = ( ITK_COORDINATE_Right << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_LAS = ( ITK_COORDINATE_Left << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )


ITK_COORDINATE_ORIENTATION_PRI = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_PLI = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ARI = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ALI = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_PRS = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_PLS = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ARS = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ALS = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_TertiaryMinor )



ITK_COORDINATE_ORIENTATION_IPR = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SPR = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_IAR = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SAR = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_IPL = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SPL = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Posterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_IAL = ( ITK_COORDINATE_Inferior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_SAL = ( ITK_COORDINATE_Superior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Anterior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )


ITK_COORDINATE_ORIENTATION_PIR = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_PSR = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_AIR = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ASR = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Right << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_PIL = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_PSL = ( ITK_COORDINATE_Posterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_AIL = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Inferior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )

ITK_COORDINATE_ORIENTATION_ASL = ( ITK_COORDINATE_Anterior << ITK_COORDINATE_PrimaryMinor ) \
                                + ( ITK_COORDINATE_Superior << ITK_COORDINATE_SecondaryMinor ) \
                                + ( ITK_COORDINATE_Left << ITK_COORDINATE_TertiaryMinor )

