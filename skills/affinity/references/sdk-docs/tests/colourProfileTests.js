'use strict';
const {
    ColourProfile,
    ColourSpaceType
} = require('/colours');

function testColourProfile() {
    for (let [name, value] of ColourSpaceType.entries) {
        console.log(name, value);
        if (value != 0) {
            console.log("Default for colour space", name);
            const defProfile = ColourProfile.getDefaultForColourSpace(value);
            console.log(defProfile.name);
            
            console.log("Available profile for colour space", name);
            const availProfiles = ColourProfile.getProfilesForColourSpace(value);
            for (let profile of availProfiles) {
                console.log(profile.name);
            }
        }
    }
}

module.exports.testColourProfile = testColourProfile;
