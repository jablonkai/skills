'use strict';
const {
    ColourProfile,
    ColourProfileSet,
} = require('/colours');


function testColourProfileSet() {
    // create the default colour profile set with either of the following
    const profileSet = ColourProfileSet.default;
    //const profileSet = ColourProfileSet.create();
    
    // get/set the intent of the profile set
    const origIntent = profileSet.intent
    profileSet.intent = 2 // Saturation
    console.log(profileSet.intent)
    profileSet.intent = origIntent
    
    // get/set use black point compensation
    const temp = profileSet.blackPointCompensation
    profileSet.blackPointCompensation = (!temp)
    console.log(profileSet.blackPointCompensation)
    profileSet.blackPointCompensation = temp
    
    
    // get profile out of the profile set / or setup your own
    var profile = profileSet.getProfileForFormat(0)
    profileSet.setProfileForFormat(1, profile)
    var newprofile = profileSet.getProfileForFormat(1)
    console.assert(profile.colourSpaceStr == newprofile.colourSpaceStr)

    // get/set profile with colour space
    var profilecs = profileSet.getProfileForColourSpaceType(3) // CMYK
    profileSet.setProfileForColourSpaceType(3, profilecs)
    var newprofilecs = profileSet.getProfileForColourSpaceType(3)
    console.assert(profilecs.colourSpaceStr == newprofilecs.colourSpaceStr)
}

module.exports.testColourProfileSet = testColourProfileSet;
