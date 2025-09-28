// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ForestAdventure {
    // Struct to store story outcome data
    struct StoryOutcome {
        uint256 storyId;
        string endingCategory;
        uint256 score;
        string imageUrl;
        string mangaImageUrl;
        address player;
        uint256 timestamp;
    }

    // Mapping to store story outcomes by ID
    mapping(uint256 => StoryOutcome) public storyOutcomes;

    // Counter for story IDs
    uint256 public storyCounter;

    // Events
    event StoryCreated(
        uint256 indexed storyId,
        address indexed player,
        string endingCategory,
        uint256 score
    );
    event StoryUpdated(uint256 indexed storyId, string newImageUrl);

    // Function to create a new story outcome
    function createStoryOutcome(
        string memory _endingCategory,
        uint256 _score,
        string memory _imageUrl,
        string memory _mangaImageUrl
    ) public returns (uint256) {
        storyCounter++;
        uint256 newStoryId = storyCounter;

        storyOutcomes[newStoryId] = StoryOutcome({
            storyId: newStoryId,
            endingCategory: _endingCategory,
            score: _score,
            imageUrl: _imageUrl,
            mangaImageUrl: _mangaImageUrl,
            player: msg.sender,
            timestamp: block.timestamp
        });

        emit StoryCreated(newStoryId, msg.sender, _endingCategory, _score);
        return newStoryId;
    }

    // Function to get story outcome details
    function getStoryOutcome(
        uint256 _storyId
    )
        public
        view
        returns (
            uint256 storyId,
            string memory endingCategory,
            uint256 score,
            string memory imageUrl,
            string memory mangaImageUrl,
            address player,
            uint256 timestamp
        )
    {
        StoryOutcome memory story = storyOutcomes[_storyId];
        return (
            story.storyId,
            story.endingCategory,
            story.score,
            story.imageUrl,
            story.mangaImageUrl,
            story.player,
            story.timestamp
        );
    }

    // Function to update story image (in case of regeneration)
    function updateStoryImage(
        uint256 _storyId,
        string memory _newImageUrl
    ) public {
        require(
            storyOutcomes[_storyId].player == msg.sender,
            "Only story owner can update"
        );
        storyOutcomes[_storyId].imageUrl = _newImageUrl;
        emit StoryUpdated(_storyId, _newImageUrl);
    }

    // Function to get total number of stories
    function getTotalStories() public view returns (uint256) {
        return storyCounter;
    }

    // Function to check if a story exists
    function storyExists(uint256 _storyId) public view returns (bool) {
        return storyOutcomes[_storyId].storyId != 0;
    }
}
